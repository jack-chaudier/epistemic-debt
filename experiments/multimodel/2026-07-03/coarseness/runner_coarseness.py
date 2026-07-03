#!/usr/bin/env python3
"""Coarseness sweep: 1-condition vs 6-condition policies, grok only.
See prereg_coarseness.md (fixed before any call)."""
import csv, json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner2 import DOMAINS, ADJ, NOUN, PARAM_T, nn_distractor, cond_clause, draw_value, full_name
from runner3 import (ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD)
from providers import chat, cost_usd

ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "coarseness_results.json")
HARD_CAP = 400
WL = 15
ALIAS = "grok"


def gen_arm(p, corpus_seed, item_seed_base):
    rng = random.Random(corpus_seed)
    patterns = [(True, None)] * 6 + [(False, k % p) for k in range(24)]
    rng.shuffle(patterns)
    codes = rng.sample([a + " " + b for a in ADJ for b in NOUN], 30)
    used_sentences, items = set(), []
    for i, (approved, fail_slot) in enumerate(patterns):
        dom = DOMAINS[i % 6]
        drng = random.Random(item_seed_base + i)
        chosen = drng.sample(dom["params"], 12)
        pol_idx = sorted(drng.sample(range(12), p))
        forbidden, plist = set(), []
        for k, pi in enumerate(pol_idx):
            name, unit, direction, lo, hi, dec = chosen[pi]
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)), 1)
            forbidden.add(float(thr))
            span = max(abs(thr) * 0.3, 0.5)
            passes = (fail_slot is None) or (k != fail_slot)
            v = draw_value(drng, thr, direction, passes, span, forbidden)
            forbidden.add(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=True, dir=direction,
                              thr=thr, value=v, passes=passes))
        for pi in range(12):
            if pi in pol_idx:
                continue
            name, unit, direction, lo, hi, dec = chosen[pi]
            for _ in range(300):
                v = round(drng.uniform(lo, hi), 2)
                if abs(v - round(v)) < 0.005 or any(abs(v - f) < 1e-9 for f in forbidden):
                    continue
                break
            else:
                raise RuntimeError("nonpolicy value draw failed")
            forbidden.add(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=False, value=v))
        plist.sort(key=lambda d: d["idx"])
        pol = [d for d in plist if d["policy"]]
        truth = "APPROVED" if all(d["passes"] for d in pol) else "DENIED"
        assert (truth == "APPROVED") == approved
        failing = None if approved else pol[fail_slot]["name"]
        code = codes[i]
        event = dom["event"].format(code=code)
        intro = (f"INCIDENT REVIEW FILE — Operation {code}. This file collects readings and "
                 f"observations logged during {event}. Entries appear in the order received by "
                 f"the Operation {code} duty desk and have not been prioritized or adjudicated.")
        param_sents = []
        for d in plist:
            for _ in range(60):
                s = drng.choice(PARAM_T).format(p=d["name"], v=d["value"], u=d["unit"],
                                                name=full_name(drng))
                if s not in used_sentences:
                    used_sentences.add(s)
                    param_sents.append(s)
                    break
            else:
                raise RuntimeError("param sentence uniqueness failed")
        body = param_sents + [nn_distractor(drng, used_sentences) for _ in range(15)]
        drng.shuffle(body)
        paras, k = [], 0
        while k < len(body):
            step = drng.choice([3, 4, 5])
            paras.append(" ".join(body[k:k + step]))
            k += step
        doc = intro + "\n\n" + "\n\n".join(paras) + "\n\nEnd of file."
        conds = " AND ".join(cond_clause(d["name"], d["unit"], d["dir"], d["thr"]) for d in pol)
        policy_text = (f"POLICY: {event[0].upper() + event[1:]} is APPROVED only if {conds}; "
                       f"otherwise it is DENIED.")
        items.append(dict(
            id=f"c{p}item{i:02d}", arm=f"p{p}", domain=dom["domain"], truth=truth,
            failing_param=failing, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            word_count=len(doc.split()), document=doc))
    return items


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["item"], r["call"])] = r
    return cache


def api(messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(ALIAS, messages)
    rec = dict(item=key_fn[0], call=key_fn[1], text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(items):
    cache = load_cache()
    comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                f"following incident file to at most {WL} words. A future analyst will need to "
                f"answer questions about this incident, but you do not know which questions. "
                f"Output only the compressed notes.")
    for it in items:
        iid = it["id"]
        summary = api([{"role": "system", "content": comp_sys},
                       {"role": "user", "content": it["document"]}], cache, (iid, "compress"))
        notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
        api([{"role": "user", "content": notes + ANS_SUFFIX}], cache, (iid, "decision"))
        api([{"role": "user", "content": notes + WHICH_SUFFIX}], cache, (iid, "which"))
        api([{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
            cache, (iid, "which_abstain"))
        print(f"{iid} done ({len(cache)})", flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def score(items):
    cache = load_cache()
    frac = lambda k, n: k / n if n else float("nan")
    rows = []
    for it in items:
        iid = it["id"]
        g = lambda call: cache.get((iid, call), {}).get("text")
        summary = g("compress")
        if summary is None:
            continue
        pol = [q for q in it["parameters"] if q["policy"]]
        fail = next((q for q in pol if not q["passes"]), None)
        m = ANS_RE.search(g("decision") or "")
        dec = m.group(1).upper() if m else None
        wp, _ = parse_which(g("which"), it["parameters"])
        wa, _ = parse_which(g("which_abstain"), it["parameters"])
        target = it["failing_param"] or "NONE"
        rows.append(dict(
            item=iid, arm=it["arm"], truth=it["truth"],
            summary_words=len(summary.split()),
            fail_retained=retained(summary, fail["value"]) if fail else None,
            decision_correct=dec == it["truth"],
            which=wp, which_correct=wp == target,
            abstained=wa == "INSUFFICIENT_EVIDENCE",
            incoherent=dec == "DENIED" and wp == "NONE"))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    out = dict(arms={}, preds={})
    for arm in ("p1", "p6"):
        den = [r for r in rows if r["arm"] == arm and r["truth"] == "DENIED"]
        lost = [r for r in den if not r["fail_retained"]]
        kept = [r for r in den if r["fail_retained"]]
        app = [r for r in rows if r["arm"] == arm and r["truth"] == "APPROVED"]
        st = dict(
            n_denied=len(den), n_lost=len(lost), n_retained=len(kept),
            applicable=len(lost) >= 8,
            which_lost=dict(k=sum(r["which_correct"] for r in lost), n=len(lost),
                            p=frac(sum(r["which_correct"] for r in lost), len(lost)),
                            ci95=wilson(sum(r["which_correct"] for r in lost), len(lost))),
            which_retained=dict(k=sum(r["which_correct"] for r in kept), n=len(kept),
                                p=frac(sum(r["which_correct"] for r in kept), len(kept))),
            abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
            abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)),
            decision_lost=frac(sum(r["decision_correct"] for r in lost), len(lost)),
            decision_denied=frac(sum(r["decision_correct"] for r in den), len(den)),
            decision_approved=frac(sum(r["decision_correct"] for r in app), len(app)),
            incoherent_lost=frac(sum(r["incoherent"] for r in lost), len(lost)))
        out["arms"][arm] = st
    a1, a6 = out["arms"]["p1"], out["arms"]["p6"]
    out["preds"] = {
        "P-S1_p1_no_reason_gap": dict(criteria="which_lost(p=1)>=0.8",
                                      value=a1["which_lost"]["p"],
                                      passed=bool(a1["which_lost"]["p"] >= 0.8)),
        "P-S2_p6_guessing": dict(criteria="which_lost(p=6)<=1/3",
                                 value=a6["which_lost"]["p"],
                                 passed=bool(a6["which_lost"]["p"] <= 1 / 3)),
        "P-S3_abstention_tracks_fiber": dict(
            criteria="abstain_lost(p=1)<=0.25 AND abstain_lost(p=6)>=0.5",
            values=dict(p1=a1["abstain_lost"], p6=a6["abstain_lost"]),
            passed=bool(a1["abstain_lost"] <= 0.25 and a6["abstain_lost"] >= 0.5)),
    }
    tok = dict(prompt=0, completion=0)
    for r in cache.values():
        tok["prompt"] += r["usage"]["prompt"]
        tok["completion"] += r["usage"]["completion"]
    out["tokens"] = tok
    out["cost_usd"] = round(cost_usd(ALIAS, tok), 4)
    for arm, st in out["arms"].items():
        print(f"{arm}: lost/ret={st['n_lost']}/{st['n_retained']} applicable={st['applicable']} "
              f"which_lost={st['which_lost']['k']}/{st['which_lost']['n']} "
              f"which_ret={st['which_retained']['k']}/{st['which_retained']['n']} "
              f"abstain_lost={st['abstain_lost']:.3f} decision_lost={st['decision_lost']:.3f}")
    for k, v in out["preds"].items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")
    print(f"cost: ${out['cost_usd']}")
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        items = gen_arm(1, 6162, 13000) + gen_arm(6, 6167, 15000)
        with open(ITEMS, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        print(f"{len(items)} items; denied per arm:",
              [sum(it['truth'] == 'DENIED' and it['arm'] == a for it in items)
               for a in ('p1', 'p6')])
    else:
        items = [json.loads(l) for l in open(ITEMS)]
        (run if cmd == "run" else score)(items)
