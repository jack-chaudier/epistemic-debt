#!/usr/bin/env python3
"""Phase B: budget sweep 5..80 words, grok, 30 DENIED v5 items.
See prereg_curve.md (fixed before any call)."""
import csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03")
V5 = os.path.join(MULTI, "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, MULTI)
from runner3 import ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX
from providers import chat, cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "curve_results.json")
HARD_CAP = 800
ALIAS = "grok"
BUDGETS = [5, 10, 15, 25, 40, 60, 80]


def comp_sys(wl):
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following incident file to at most {wl} words. A future analyst will need to "
            f"answer questions about this incident, but you do not know which questions. "
            f"Output only the compressed notes.")


def load_items():
    return [it for it in map(json.loads, open(os.path.join(V5, "items.jsonl")))
            if it["truth"] == "DENIED"]


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["wl"], r["item"], r["call"])] = r
    return cache


def api(messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(ALIAS, messages)
    rec = dict(wl=key_fn[0], item=key_fn[1], call=key_fn[2], text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(items):
    cache = load_cache()
    for wl in BUDGETS:
        for it in items:
            iid = it["id"]
            summary = api([{"role": "system", "content": comp_sys(wl)},
                           {"role": "user", "content": it["document"]}],
                          cache, (wl, iid, "compress"))
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api([{"role": "user", "content": notes + ANS_SUFFIX}], cache, (wl, iid, "decision"))
            api([{"role": "user", "content": notes + WHICH_SUFFIX}], cache, (wl, iid, "which"))
        print(f"budget {wl} done ({len(cache)})", flush=True)


def score(items):
    cache = load_cache()
    frac = lambda k, n: k / n if n else float("nan")
    rows = []
    for wl in BUDGETS:
        for it in items:
            iid = it["id"]
            r = cache.get((wl, iid, "compress"))
            if r is None:
                continue
            summary = r["text"]
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next(p for p in pol if not p["passes"])
            m = ANS_RE.search(cache.get((wl, iid, "decision"), {}).get("text") or "")
            wp, _ = parse_which(cache.get((wl, iid, "which"), {}).get("text"), it["parameters"])
            rows.append(dict(
                wl=wl, item=iid, realized_words=len(summary.split()),
                ret_policy=sum(retained(summary, p["value"]) for p in pol) / 3,
                fail_retained=retained(summary, fail["value"]),
                decision_correct=(m.group(1).upper() if m else None) == "DENIED",
                which_correct=wp == it["failing_param"]))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    curve = {}
    for wl in BUDGETS:
        sub = [r for r in rows if r["wl"] == wl]
        curve[wl] = dict(
            n=len(sub),
            realized_words=sum(r["realized_words"] for r in sub) / len(sub),
            retention=sum(r["ret_policy"] for r in sub) / len(sub),
            fail_survival=frac(sum(r["fail_retained"] for r in sub), len(sub)),
            decision=frac(sum(r["decision_correct"] for r in sub), len(sub)),
            which=frac(sum(r["which_correct"] for r in sub), len(sub)))
    dec = {wl: c["decision"] for wl, c in curve.items()}
    whi = {wl: c["which"] for wl, c in curve.items()}
    mono = all(whi[BUDGETS[i + 1]] >= whi[BUDGETS[i]] - 0.10 for i in range(len(BUDGETS) - 1))
    shelf_set = [wl for wl in BUDGETS if dec[wl] >= 0.75 and whi[wl] <= 0.5]
    preds = {
        "P-B1_answer_saturates": dict(values=dec,
                                      passed=bool(all(v >= 0.75 for v in dec.values()))),
        "P-B2_reason_monotone": dict(values=whi, monotone=mono,
                                     passed=bool(mono and whi[5] <= 0.2 and whi[80] >= 0.8)),
        "P-B3_wide_shelf": dict(shelf_budgets=shelf_set,
                                passed=bool(all(w in shelf_set for w in (5, 10, 15)))),
    }
    # exploratory logistic fit of WHICH vs realized words (no scipy; grid MLE)
    pts = [(r["realized_words"], r["which_correct"]) for r in rows]
    best = None
    for mid in [x * 2.0 for x in range(1, 46)]:
        for slope in [x * 0.05 for x in range(1, 60)]:
            ll = 0.0
            for x, y in pts:
                p = 1 / (1 + math.exp(-slope * (x - mid)))
                p = min(max(p, 1e-9), 1 - 1e-9)
                ll += math.log(p) if y else math.log(1 - p)
            if best is None or ll > best[0]:
                best = (ll, mid, slope)
    fit = dict(midpoint_words=best[1], slope=best[2], loglik=round(best[0], 2),
               note="exploratory grid MLE, WHICH vs realized words")
    tok = dict(prompt=0, completion=0)
    for r in cache.values():
        tok["prompt"] += r["usage"]["prompt"]
        tok["completion"] += r["usage"]["completion"]
    cost = round(cost_usd(ALIAS, tok), 4)
    print(f"{'wl':>4} {'real':>6} {'ret':>6} {'failsv':>7} {'dec':>6} {'which':>6}")
    for wl in BUDGETS:
        c = curve[wl]
        print(f"{wl:>4} {c['realized_words']:>6.1f} {c['retention']:>6.3f} "
              f"{c['fail_survival']:>7.3f} {c['decision']:>6.3f} {c['which']:>6.3f}")
    for k, v in preds.items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")
    print(f"  logistic fit: midpoint={fit['midpoint_words']}w slope={fit['slope']}")
    print(f"cost: ${cost}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(model=ALIAS, budgets=BUDGETS, n_items=len(items),
                                   prereg="prereg_curve.md"),
                       curve={str(k): v for k, v in curve.items()},
                       preds=preds, logistic_fit=fit, tokens=tok, cost_usd=cost), f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    items = load_items()
    (run if sys.argv[1] == "run" else score)(items)
