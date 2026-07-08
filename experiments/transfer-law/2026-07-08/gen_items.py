#!/usr/bin/env python3
"""Law-3 cached-summary pilot corpus: counterfactual policies over existing domain items.

This generator reuses the 2026-07-06 domain-battery documents and cached summaries, then
adds a fresh counterfactual policy over three originally non-policy readings. The point is
to test whether a summary that preserved the original answer also retained enough witness
state to recompute after a policy change.

No LLM calls. Deterministic. Writes items.jsonl next to this file.
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

SOURCE_ITEMS = os.path.join(REPO, "experiments", "domains", "2026-07-06", "items.jsonl")
ITEMS = os.path.join(HERE, "items.jsonl")
DOMAINS = ["ops_incident", "clinical_enroll", "ci_release"]
N_PER_DOMAIN = 30
SEED = 708010

SPEC_BY_DOMAIN = {
    key: {p[0]: p for p in spec["params"]}
    for key, spec in D.DOMAINS.items()
}


def load_source_items():
    if not os.path.exists(SOURCE_ITEMS):
        raise SystemExit("source domain items missing; expected experiments/domains/2026-07-06/items.jsonl")
    return [json.loads(line) for line in open(SOURCE_ITEMS)]


def value_unique_for_retained(item, value):
    values = [p["value"] for p in item["parameters"]]
    return sum(retained(str(v), value) for v in values) == 1


def threshold_for(value, direction, want_pass, lo, hi, dec):
    value = float(value)
    delta = max((hi - lo) * 0.08, 1.0 if dec == 0 else 0.1)
    if direction == "max":
        raw = value + delta if want_pass else value - delta
    else:
        raw = value - delta if want_pass else value + delta
    if dec == 0:
        thr = int(round(raw))
        if (direction == "max" and ((value <= thr) != want_pass)) or \
           (direction == "min" and ((value >= thr) != want_pass)):
            thr += 1 if want_pass == (direction == "max") else -1
        return thr
    thr = round(raw, dec)
    if (direction == "max" and ((value <= thr) != want_pass)) or \
       (direction == "min" and ((value >= thr) != want_pass)):
        bump = 10 ** (-dec)
        thr += bump if want_pass == (direction == "max") else -bump
        thr = round(thr, dec)
    return thr


def choose_source_subset(items, domain, rng):
    ditems = [it for it in items if it["domain"] == domain]
    approved = [it for it in ditems if it["truth"] == "APPROVED"]
    denied = [it for it in ditems if it["truth"] == "DENIED"]
    half = N_PER_DOMAIN // 2
    chosen = rng.sample(approved, half) + rng.sample(denied, N_PER_DOMAIN - half)
    rng.shuffle(chosen)
    return chosen


def build_cf_item(src, cf_id, pattern, rng):
    approved, fail_slot = pattern
    candidates = [p for p in src["parameters"] if not p["policy"] and value_unique_for_retained(src, p["value"])]
    rng.shuffle(candidates)
    chosen = []
    for p in candidates:
        if p["name"] in SPEC_BY_DOMAIN[src["domain"]]:
            chosen.append(p)
        if len(chosen) == 3:
            break
    if len(chosen) < 3:
        raise RuntimeError(f"{src['id']}: fewer than three unique non-policy counterfactual candidates")

    cf_params = []
    for slot, p in enumerate(chosen):
        name, unit, direction, lo, hi, dec = SPEC_BY_DOMAIN[src["domain"]][p["name"]]
        passes = approved or slot != fail_slot
        thr = threshold_for(p["value"], direction, passes, lo, hi, dec)
        cf_params.append(dict(name=name, unit=unit, value=p["value"], dir=direction,
                              thr=thr, passes=passes, slot=slot))
    cf_truth = "APPROVED" if all(p["passes"] for p in cf_params) else "DENIED"
    cf_failing = next((p["name"] for p in cf_params if not p["passes"]), None)
    event = src["event"] + " under the revised review policy"
    policy = (f"COUNTERFACTUAL POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
              f"{cond_clause(cf_params[0]['name'], cf_params[0]['unit'], cf_params[0]['dir'], cf_params[0]['thr'])} AND "
              f"{cond_clause(cf_params[1]['name'], cf_params[1]['unit'], cf_params[1]['dir'], cf_params[1]['thr'])} AND "
              f"{cond_clause(cf_params[2]['name'], cf_params[2]['unit'], cf_params[2]['dir'], cf_params[2]['thr'])}; "
              f"otherwise it is DENIED.")
    return dict(
        id=cf_id,
        domain=src["domain"],
        source_id=src["id"],
        source_truth=src["truth"],
        source_failing_param=src["failing_param"],
        cf_truth=cf_truth,
        cf_failing_param=cf_failing,
        cf_fail_slot=fail_slot,
        source_policy_text=src["policy_text"],
        cf_policy_text=policy,
        cf_parameters=cf_params,
        source_parameters=src["parameters"],
        document=src["document"],
        word_count=src["word_count"],
    )


def selfcheck(items):
    problems = []
    for it in items:
        if len(it["cf_parameters"]) != 3:
            problems.append((it["id"], "bad-cf-param-count"))
        if it["cf_truth"] == "DENIED":
            fails = [p for p in it["cf_parameters"] if not p["passes"]]
            if len(fails) != 1 or fails[0]["name"] != it["cf_failing_param"]:
                problems.append((it["id"], "bad-denied-fail-count"))
        for p in it["cf_parameters"]:
            hits = sum(retained(str(src_p["value"]), p["value"]) for src_p in it["source_parameters"])
            if hits != 1:
                problems.append((it["id"], "cf-value-collision", p["name"], p["value"], hits))
            ok = (float(p["value"]) <= float(p["thr"])) if p["dir"] == "max" else (float(p["value"]) >= float(p["thr"]))
            if ok != p["passes"]:
                problems.append((it["id"], "threshold-truth-mismatch", p["name"]))
    return problems


def main():
    src_items = load_source_items()
    rng = random.Random(SEED)
    patterns = [(True, None)] * (N_PER_DOMAIN // 2) + [(False, k % 3) for k in range(N_PER_DOMAIN // 2)]
    out = []
    for domain in DOMAINS:
        local_patterns = list(patterns)
        rng.shuffle(local_patterns)
        chosen = choose_source_subset(src_items, domain, rng)
        for j, src in enumerate(chosen):
            out.append(build_cf_item(src, f"{domain}-cf-{j:03d}", local_patterns[j], rng))
    problems = selfcheck(out)
    if problems:
        print(f"SELFCHECK FAILED ({len(problems)}):")
        for p in problems[:20]:
            print("  ", p)
        sys.exit(1)
    with open(ITEMS, "w") as f:
        for it in out:
            f.write(json.dumps(it) + "\n")
    print(f"wrote {len(out)} counterfactual items ({len(DOMAINS)} domains x {N_PER_DOMAIN})")
    for domain in DOMAINS:
        ds = [it for it in out if it["domain"] == domain]
        print(f"  {domain:16} n={len(ds)} cf_DENIED={sum(it['cf_truth'] == 'DENIED' for it in ds)}")
    print("selfcheck: clean")


if __name__ == "__main__":
    main()
