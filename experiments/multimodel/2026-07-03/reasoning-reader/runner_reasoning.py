#!/usr/bin/env python3
"""Reasoning-reader arm: gpt-5-mini answers from grok's cached v5 summaries.
See prereg_reasoning.md (fixed before any call)."""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, "..", "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner3 import (ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD)
from providers import chat, cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "reasoning_results.json")
HARD_CAP = 400
ALIAS = "gpt5mini"
COMPRESSOR = "grok"


def load_inputs():
    items = [json.loads(l) for l in open(os.path.join(V5, "items.jsonl"))]
    sums = {}
    for line in open(os.path.join(V5, "responses_raw.jsonl")):
        r = json.loads(line)
        if r["model"] == COMPRESSOR and r["call"] == "compress":
            sums[r["item"]] = r["text"]
    return items, sums


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


def run():
    items, sums = load_inputs()
    cache = load_cache()
    for it in items:
        iid = it["id"]
        notes = it["policy_text"] + "\n\nCompressed case notes:\n" + sums[iid] + "\n\n"
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


def score():
    items, sums = load_inputs()
    cache = load_cache()
    frac = lambda k, n: k / n if n else float("nan")
    rows = []
    for it in items:
        iid = it["id"]
        g = lambda call: cache.get((iid, call), {}).get("text")
        if g("decision") is None:
            continue
        pol = [q for q in it["parameters"] if q["policy"]]
        fail = next((q for q in pol if not q["passes"]), None)
        m = ANS_RE.search(g("decision") or "")
        dec = m.group(1).upper() if m else None
        wp, _ = parse_which(g("which"), it["parameters"])
        wa, _ = parse_which(g("which_abstain"), it["parameters"])
        target = it["failing_param"] or "NONE"
        rows.append(dict(
            item=iid, truth=it["truth"],
            fail_retained=retained(sums[iid], fail["value"]) if fail else None,
            decision_correct=dec == it["truth"],
            which=wp, which_correct=wp == target,
            which_confab=(wp not in (None, "NONE", "INSUFFICIENT_EVIDENCE", "UNMATCHED")
                          and wp != target),
            abstained=wa == "INSUFFICIENT_EVIDENCE",
            incoherent=dec == "DENIED" and wp == "NONE"))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    den = [r for r in rows if r["truth"] == "DENIED"]
    lost = [r for r in den if not r["fail_retained"]]
    kept = [r for r in den if r["fail_retained"]]
    cells = dict(
        n=len(rows), n_lost=len(lost), n_retained=len(kept),
        which_lost=dict(k=sum(r["which_correct"] for r in lost), n=len(lost),
                        p=frac(sum(r["which_correct"] for r in lost), len(lost)),
                        ci95=wilson(sum(r["which_correct"] for r in lost), len(lost))),
        which_retained=dict(k=sum(r["which_correct"] for r in kept), n=len(kept),
                            p=frac(sum(r["which_correct"] for r in kept), len(kept)),
                            ci95=wilson(sum(r["which_correct"] for r in kept), len(kept))),
        decision_lost=frac(sum(r["decision_correct"] for r in lost), len(lost)),
        abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
        abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)),
        incoherent_lost=frac(sum(r["incoherent"] for r in lost), len(lost)),
        which_confab_lost=frac(sum(r["which_confab"] for r in lost), len(lost)))
    preds = {
        "P-R1_no_recovery": dict(
            criteria="which_lost<=1/3 AND which_retained>=0.7",
            values=dict(which_lost=cells["which_lost"]["p"],
                        which_retained=cells["which_retained"]["p"]),
            passed=bool(cells["which_lost"]["p"] <= 1 / 3
                        and cells["which_retained"]["p"] >= 0.7)),
        "P-R2_honesty": dict(
            criteria="abstain_lost>=0.5 AND abstain_retained<=0.1",
            values=dict(abstain_lost=cells["abstain_lost"],
                        abstain_retained=cells["abstain_retained"]),
            passed=bool(cells["abstain_lost"] >= 0.5 and cells["abstain_retained"] <= 0.1)),
        "P-R3_verdict_persists": dict(
            criteria="decision_lost>=0.6", values=dict(decision_lost=cells["decision_lost"]),
            passed=bool(cells["decision_lost"] >= 0.6)),
    }
    tok = dict(prompt=0, completion=0)
    for r in cache.values():
        tok["prompt"] += r["usage"]["prompt"]
        tok["completion"] += r["usage"]["completion"]
    cost = round(cost_usd(ALIAS, tok), 4)
    print(json.dumps(cells, indent=1))
    for k, v in preds.items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}  {v['values']}")
    print(f"cost: ${cost}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(answerer="gpt-5-mini (reasoning, default effort, temp fixed at 1 by API)",
                                   compressor=COMPRESSOR, prereg="prereg_reasoning.md"),
                       cells=cells, preds=preds, tokens=tok, cost_usd=cost), f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    (run if sys.argv[1] == "run" else score)()
