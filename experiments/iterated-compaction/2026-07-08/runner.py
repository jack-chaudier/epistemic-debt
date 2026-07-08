#!/usr/bin/env python3
"""Iterated compaction — the epistemic interest rate. See prereg_iterated_compaction.md.

Fixed budget W=40 words, R=4 rounds (doc->S1->S2->S3->S4), same contract-blind instruction each
round. Per round: measure witness survival S_r (string check), failing-value survival, decision-
probe verdict persistence, realized length L_r. Interest rate rho = S_(r+1)/S_r.

  smoke --model grok      # 3 items, all rounds, prints raw summaries
  run   --model grok|haiku|gpt [--limit N]
  score                   # per-model decay curve, rho, predictions pass/fail

Idempotent cache keyed by (model,item,call); hard cap 2000/model. Stdlib only; temperature 0.
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v2"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from runner3 import ANS_RE, retained  # noqa: E402
from providers import chat, cost_usd  # noqa: E402

DOMAIN_ITEMS = os.path.join(HERE, "..", "..", "domains", "2026-07-06", "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "iterated_compaction_results.json")
MODELS = ["grok", "haiku", "gpt"]
W = 40
R = 4
N_ITEMS = 40
DOMAINS_USED = ["ops_incident", "clinical_enroll", "ci_release"]
HARD_CAP = 2000
GIST_RE = __import__("re").compile(
    r"anomal|exceed|below|out[- ]of[- ]spec|out of range|marginal|elevated|degraded|warning|"
    r"abnormal|deviat|breach|violat|fail|flag|too (high|low)|noncompliant|non-compliant", __import__("re").I)

PREDICTIONS = {
    "P-IC-0_budget_binds": "round-1 realized length >= 0.70*W (>=28 words)",
    "P-IC-1_monotone_decay": "S non-increasing (tol 0.03) AND S4 < S1 - 0.10",
    "P-IC-2_gist_persists": "g4 >= g1 - 0.10 while S4 < S1 - 0.10",
    "P-IC-3_stable_ratio": "successive rho = S(r+1)/S(r) span (max-min) <= 0.20",
}


def comp_sys(kind):
    src = "incident file" if kind == "doc" else "case notes"
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following {src} to at most {W} words. A future analyst will need to answer questions "
            f"about this incident, but you do not know which questions. Output only the compressed notes.")


DECISION = " Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED or ANSWER: DENIED."


def load_items():
    all_items = [json.loads(l) for l in open(DOMAIN_ITEMS)]
    out = []
    per = N_ITEMS // len(DOMAINS_USED)
    extra = N_ITEMS - per * len(DOMAINS_USED)
    for di, dom in enumerate(DOMAINS_USED):
        denied = [it for it in all_items if it["domain"] == dom and it["truth"] == "DENIED"]
        take = per + (1 if di < extra else 0)
        out.extend(denied[:take])
    return out


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def run_model(alias, items):
    cache = load_cache()
    n0 = len(cache)

    def api(call, messages):
        key = (alias, iid, call)
        if key in cache:
            return cache[key]["text"]
        if len(cache) - n0 + 1 > HARD_CAP:
            sys.exit(f"HARD CAP {HARD_CAP} for {alias}")
        text, usage = chat(alias, messages)
        rec = dict(model=alias, item=iid, call=call, text=text, usage=usage)
        with open(RAW, "a") as f:
            f.write(json.dumps(rec) + "\n")
        cache[key] = rec
        return text

    for n, it in enumerate(items):
        iid = it["id"]
        prev, kind = it["document"], "doc"
        for r in range(1, R + 1):
            summary = api(f"compress{r}", [{"role": "system", "content": comp_sys(kind)},
                                           {"role": "user", "content": prev}])
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(f"decision{r}", [{"role": "user", "content": notes + DECISION}])
            prev, kind = summary, "notes"
        if (n + 1) % 20 == 0:
            print(f"  {alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


def do_score():
    items = load_items()
    cache = load_cache()
    models = sorted({k[0] for k in cache}) or MODELS
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]
    out = {"design": dict(W=W, R=R, n_items=len(items), domains=DOMAINS_USED,
                          predictions=PREDICTIONS), "per_model": {}}
    for alias in models:
        rounds = {r: dict(S=[], fail=[], L=[], gverdict=[], ggist=[]) for r in range(1, R + 1)}
        n_scored = 0
        for it in items:
            g = lambda call: cache.get((alias, it["id"], call), {}).get("text")
            if g("compress1") is None:
                continue
            n_scored += 1
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            for r in range(1, R + 1):
                s = g(f"compress{r}") or ""
                rounds[r]["S"].append(sum(retained(s, p["value"]) for p in pol) / len(pol))
                if fail:
                    rounds[r]["fail"].append(1.0 if retained(s, fail["value"]) else 0.0)
                rounds[r]["L"].append(len(s.split()))
                rounds[r]["ggist"].append(1.0 if GIST_RE.search(s) else 0.0)
                dt = g(f"decision{r}") or ""
                m = ANS_RE.search(dt)
                rounds[r]["gverdict"].append(1.0 if (m and m.group(1).upper() == it["truth"]) else 0.0)
        mean = lambda xs: (round(sum(xs) / len(xs), 4) if xs else None)
        curve = {r: dict(S=mean(rounds[r]["S"]), fail=mean(rounds[r]["fail"]),
                         L=mean(rounds[r]["L"]), gverdict=mean(rounds[r]["gverdict"]),
                         ggist=mean(rounds[r]["ggist"])) for r in range(1, R + 1)}
        S = [curve[r]["S"] for r in range(1, R + 1)]
        L1 = curve[1]["L"]
        # rho ratios where S_r >= 0.15
        ratios = []
        for r in range(1, R):
            if S[r - 1] is not None and S[r - 1] >= 0.15 and S[r] is not None:
                ratios.append(round(S[r] / S[r - 1], 4))
        rho_bar = round(math.exp(sum(math.log(x) for x in ratios) / len(ratios)), 4) if ratios else None

        p0 = bool(L1 is not None and L1 >= 0.70 * W)
        monotone = all(S[r] <= S[r - 1] + 0.03 for r in range(1, R) if S[r] is not None and S[r - 1] is not None)
        net = bool(S[0] is not None and S[-1] is not None and S[-1] < S[0] - 0.10)
        p1 = bool(monotone and net)
        g1, g4 = curve[1]["gverdict"], curve[R]["gverdict"]
        p2 = bool(g1 is not None and g4 is not None and g4 >= g1 - 0.10 and net)
        p3 = bool(ratios and (max(ratios) - min(ratios)) <= 0.20)
        shelf_widen = None
        if None not in (g1, g4, S[0], S[-1]):
            shelf_widen = round((g4 - S[-1]) - (g1 - S[0]), 4)
        out["per_model"][alias] = dict(
            n_scored=n_scored, curve=curve, S_curve=S, rho_ratios=ratios, rho_bar=rho_bar,
            shelf_widening=shelf_widen,
            predictions={
                "P-IC-0_budget_binds": dict(L1=L1, passed=p0),
                "P-IC-1_monotone_decay": dict(S1=S[0], S4=S[-1], monotone=monotone, net_decay=net, passed=p1),
                "P-IC-2_gist_persists": dict(g1=g1, g4=g4, S1=S[0], S4=S[-1], passed=p2),
                "P-IC-3_stable_ratio": dict(ratios=ratios, span=(round(max(ratios) - min(ratios), 4) if ratios else None), rho_bar=rho_bar, passed=p3),
            },
            cost_usd=round(cost_usd(alias, tok[alias]), 4))

    applicable = {m: out["per_model"][m]["predictions"]["P-IC-0_budget_binds"]["passed"] for m in out["per_model"]}
    law = {m: all(out["per_model"][m]["predictions"][k]["passed"] for k in
                  ("P-IC-1_monotone_decay", "P-IC-2_gist_persists", "P-IC-3_stable_ratio"))
           for m in out["per_model"] if applicable[m]}
    out["verdict"] = dict(
        applicable=applicable,
        interest_rate_confirmed_on=[m for m, v in law.items() if v],
        rho_bar={m: out["per_model"][m]["rho_bar"] for m in out["per_model"]},
        confirmed=bool(sum(law.values()) >= 2))
    out["cost_usd"] = {m: out["per_model"][m]["cost_usd"] for m in out["per_model"]}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    for alias in models:
        pm = out["per_model"][alias]
        print(f"\n=== {alias} === (n={pm['n_scored']}, cost ${pm['cost_usd']})")
        print(f"  S curve: {pm['S_curve']}  rho_ratios={pm['rho_ratios']}  rho_bar={pm['rho_bar']}")
        print(f"  L1={pm['curve'][1]['L']}  gverdict {pm['curve'][1]['gverdict']}->{pm['curve'][R]['gverdict']}  "
              f"shelf_widening={pm['shelf_widening']}")
        for k, v in pm["predictions"].items():
            print(f"    {'PASS' if v['passed'] else 'FAIL'}  {k}")
    print(f"\nverdict: {json.dumps(out['verdict'])}")
    print(f"total cost: ${out['total_cost_usd']}")
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    items = load_items()
    if a.cmd == "smoke":
        items = items[:3]
        run_model(a.model, items)
        cache = load_cache()
        for it in items:
            print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']!r}")
            for r in range(1, R + 1):
                s = cache.get((a.model, it["id"], f"compress{r}"), {}).get("text", "")
                d = cache.get((a.model, it["id"], f"decision{r}"), {}).get("text", "")
                print(f"  S{r} ({len(s.split())}w): {s.strip()[:180]}")
                print(f"     dec{r}: {d.strip()[:60]}")
        return
    if a.limit:
        items = items[:a.limit]
    run_model(a.model, items)
    print(f"{a.model} done ({len(items)} items)")


if __name__ == "__main__":
    main()
