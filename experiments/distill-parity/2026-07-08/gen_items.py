#!/usr/bin/env python3
"""Distill-parity corpora: train pool + every eval set, per the FROZEN prereg (d24e198).

Splits (all deterministic; seed family 812xxx is fresh and disjoint from every prior
campaign: 706010, 70602x, 708010, 20260708, 78080x, 90210):

  train_pool.jsonl     6 domains x 1000 = 6000 items (50/50 verdict by construction; G2/G3
                       filtering on the pod must leave >= 3000 or the campaign STOPs)
  parity_gauge.jsonl   6 x 60  = 360  held-out full-document parity items   (prereg >= 300)
  dev_slice.jsonl      6 x 50  = 300  checkpoint-selection slice, never reported
  delta_battery.jsonl  6 x 200 = 1200 dissociation items (targets >= 200 lost + >= 200
                       retained cells per model; reserve below tops up short cells)
  delta_reserve.jsonl  6 x 100 = 600  deterministic extension, used only if a cell < 200
  arm3.jsonl           6 x 30  = 180  counterfactual items (cf policy over 3 originally
                       non-policy readings; full-doc Arm 3a and compressed Arm 3b share
                       these items, cf-verdict balanced)                    (prereg >= 150/90)

Every split is re-id'd with its split prefix so ids never collide across splits. Realdoc arm
reuses experiments/realdoc/2026-07-08/items.jsonl unchanged (row 31). Capability slice
(250 GSM8K + 250 MMLU) is built on the pod by build_capability.py (public datasets, seeded).
No LLM calls. Selfcheck (lib/domains + cf selfcheck) must be clean before writing.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "lib"))
import domains as D  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v2"))
from runner2 import cond_clause  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained  # noqa: E402

SPLITS = [  # (name, per-domain seed base, n per domain)
    ("trainpool", 812100, 1000),
    ("parity", 812200, 60),
    ("dev", 812300, 50),
    ("delta", 812400, 200),
    ("deltares", 812500, 100),
]
ARM3_SRC_SEED = 812600   # per-domain source items for the counterfactual arm
ARM3_CF_SEED = 812700    # cf-policy construction
ARM3_PER_DOMAIN = 30

SPEC_BY_DOMAIN = {key: {p[0]: p for p in spec["params"]} for key, spec in D.DOMAINS.items()}


def gen_domain(key, seed0, n):
    """Chunked generation (<=250/chunk, the proven prior-campaign scale) with a deterministic
    seed-retry rule: chunk k uses seed0 + 600000*k; a chunk whose rejection sampler fails is
    skipped and k advances. Deterministic in (key, seed0, n); each chunk is verdict-balanced."""
    items, k, got = [], 0, 0
    while got < n:
        m = min(250, n - got)
        try:
            batch = D.gen_items(key, seed=seed0 + 600000 * k, n=m)
        except RuntimeError:
            k += 1
            continue
        items.extend(batch)
        got += m
        k += 1
    return items


def gen_split(name, seed_base, n_per_domain):
    items = []
    for idx, key in enumerate(D.DOMAIN_KEYS):
        batch = gen_domain(key, seed_base + idx, n_per_domain)
        for j, it in enumerate(batch):
            it["id"] = f"{name}-{key}-{j:04d}"
            it["split"] = name
        items.extend(batch)
    problems = D.selfcheck(items)
    if problems:
        print(f"SELFCHECK FAILED for {name} ({len(problems)}):")
        for p in problems[:20]:
            print("  ", p)
        sys.exit(1)
    return items


def value_unique(item, value):
    return sum(retained(str(p["value"]), value) for p in item["parameters"]) == 1


def threshold_for(value, direction, want_pass, lo, hi, dec):
    value = float(value)
    delta = max((hi - lo) * 0.08, 1.0 if dec == 0 else 0.1)
    raw = value + delta if (direction == "max") == want_pass else value - delta
    thr = int(round(raw)) if dec == 0 else round(raw, dec)
    ok = (value <= thr) if direction == "max" else (value >= thr)
    if ok != want_pass:
        bump = 1 if dec == 0 else 10 ** (-dec)
        thr += bump if want_pass == (direction == "max") else -bump
        thr = thr if dec == 0 else round(thr, dec)
    return thr


def build_cf(src, cf_id, pattern, rng):
    approved, fail_slot = pattern
    cands = [p for p in src["parameters"] if not p["policy"] and value_unique(src, p["value"])
             and p["name"] in SPEC_BY_DOMAIN[src["domain"]]]
    rng.shuffle(cands)
    if len(cands) < 3:
        raise RuntimeError(f"{src['id']}: <3 cf candidates")
    chosen = cands[:3]
    cf_params = []
    for slot, p in enumerate(chosen):
        name, unit, direction, lo, hi, dec = SPEC_BY_DOMAIN[src["domain"]][p["name"]]
        passes = approved or slot != fail_slot
        thr = threshold_for(p["value"], direction, passes, lo, hi, dec)
        cf_params.append(dict(name=name, unit=unit, value=p["value"], dir=direction,
                              thr=thr, passes=passes, slot=slot))
    cf_truth = "APPROVED" if all(p["passes"] for p in cf_params) else "DENIED"
    event = src["event"] + " under the revised review policy"
    policy = (f"COUNTERFACTUAL POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
              f"{cond_clause(cf_params[0]['name'], cf_params[0]['unit'], cf_params[0]['dir'], cf_params[0]['thr'])} AND "
              f"{cond_clause(cf_params[1]['name'], cf_params[1]['unit'], cf_params[1]['dir'], cf_params[1]['thr'])} AND "
              f"{cond_clause(cf_params[2]['name'], cf_params[2]['unit'], cf_params[2]['dir'], cf_params[2]['thr'])}; "
              f"otherwise it is DENIED.")
    out = dict(src)
    out.update(id=cf_id, split="arm3", cf_truth=cf_truth,
               cf_failing_param=next((p["name"] for p in cf_params if not p["passes"]), None),
               cf_fail_slot=fail_slot, cf_policy_text=policy, cf_parameters=cf_params)
    return out


def cf_selfcheck(items):
    problems = []
    for it in items:
        if it["cf_truth"] == "DENIED":
            fails = [p for p in it["cf_parameters"] if not p["passes"]]
            if len(fails) != 1 or fails[0]["name"] != it["cf_failing_param"]:
                problems.append((it["id"], "bad-denied-fail-count"))
        for p in it["cf_parameters"]:
            hits = sum(retained(str(sp["value"]), p["value"]) for sp in it["parameters"])
            if hits != 1:
                problems.append((it["id"], "cf-value-collision", p["name"], hits))
            ok = (float(p["value"]) <= float(p["thr"])) if p["dir"] == "max" \
                else (float(p["value"]) >= float(p["thr"]))
            if ok != p["passes"]:
                problems.append((it["id"], "threshold-truth-mismatch", p["name"]))
    return problems


def main():
    manifest = {}
    for name, seed_base, n in SPLITS:
        items = gen_split(name, seed_base, n)
        path = os.path.join(HERE, {"trainpool": "train_pool", "parity": "parity_gauge",
                                   "dev": "dev_slice", "delta": "delta_battery",
                                   "deltares": "delta_reserve"}[name] + ".jsonl")
        with open(path, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        den = sum(it["truth"] == "DENIED" for it in items)
        manifest[name] = dict(n=len(items), denied=den, seed_base=seed_base,
                              words_mean=round(sum(i["word_count"] for i in items) / len(items)))
        print(f"{name:10} n={len(items):5} DENIED={den:5} -> {os.path.basename(path)}")

    # Arm 3: fresh source items, then cf policies (verdict-balanced within each domain).
    src = gen_split("arm3src", ARM3_SRC_SEED, ARM3_PER_DOMAIN)
    rng = random.Random(ARM3_CF_SEED)
    half = ARM3_PER_DOMAIN // 2
    out = []
    for key in D.DOMAIN_KEYS:
        patterns = [(True, None)] * half + [(False, k % 3) for k in range(ARM3_PER_DOMAIN - half)]
        rng.shuffle(patterns)
        ditems = [it for it in src if it["domain"] == key]
        for j, s in enumerate(ditems):
            out.append(build_cf(s, f"arm3-{key}-{j:03d}", patterns[j], rng))
    problems = cf_selfcheck(out)
    if problems:
        print(f"CF SELFCHECK FAILED ({len(problems)}):")
        for p in problems[:20]:
            print("  ", p)
        sys.exit(1)
    with open(os.path.join(HERE, "arm3.jsonl"), "w") as f:
        for it in out:
            f.write(json.dumps(it) + "\n")
    manifest["arm3"] = dict(n=len(out), cf_denied=sum(i["cf_truth"] == "DENIED" for i in out),
                            src_seed=ARM3_SRC_SEED, cf_seed=ARM3_CF_SEED)
    print(f"arm3       n={len(out):5} cf_DENIED={manifest['arm3']['cf_denied']:5} -> arm3.jsonl")

    with open(os.path.join(HERE, "corpus_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print("selfcheck: clean on all splits")


if __name__ == "__main__":
    main()
