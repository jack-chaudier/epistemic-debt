#!/usr/bin/env python3
"""Phase 1: the Justification Budget Line J = S(artifact).

Budget sweep {5,10,15,25,40,60,80} words on 30 DENIED items, per (model, corpus)
arm. Reader = compressor. Tests slope-1 / intercept-0 of justified accuracy (WHICH)
vs witness survival (failing-value string retention). See prereg_budgetline.md.

  run --model haiku|gpt|grok --corpus incident|clinical
  score        # aggregates every cached arm, fits the line, writes results json
"""
import argparse, csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03")
V5 = os.path.join(MULTI, "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, MULTI)
from runner3 import ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX
from providers import chat, cost_usd
from clinical_match import resolve_which

RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "budgetline_results.json")
HARD_CAP = 3400
BUDGETS = [5, 10, 15, 25, 40, 60, 80]
# WHICH probe standardizes output format across the medical-abbreviation domain;
# scoring additionally resolves clinical shorthand (clinical_match). Fixed before spend.
WHICH_PROBE = WHICH_SUFFIX + " Use the parameter's full name exactly as written in the policy above."
CORPORA = {
    "incident": os.path.join(V5, "items.jsonl"),
    "clinical": os.path.join(HERE, "items_clinical.jsonl"),
}
# 4 confirmatory arms per prereg_budgetline.md; the cached Phase B grok/incident curve is
# the reference arm (prior evidence, scored for context, excluded from the campaign count).
# 2026-07-06 post-hoc bugfix, disclosed in README: the original list also contained
# ("grok","incident"), so score() double-counted the reference as confirmatory (of=5) and
# duplicated its rows in scored.csv. Verdict unaffected (law fails 1/4 and 1/5 alike).
ARMS = [("haiku", "incident"), ("gpt", "incident"),
        ("grok", "clinical"), ("gpt", "clinical")]
REFERENCE = ("grok", "incident")


def comp_sys(wl):
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following incident file to at most {wl} words. A future analyst will need to "
            f"answer questions about this incident, but you do not know which questions. "
            f"Output only the compressed notes.")


def load_items(corpus):
    return [it for it in map(json.loads, open(CORPORA[corpus])) if it["truth"] == "DENIED"]


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["model"], r["corpus"], r["wl"], r["item"], r["call"])] = r
    return cache


def api(alias, corpus, messages, cache, key):
    if key in cache:
        return cache[key]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(alias, messages)
    rec = dict(model=alias, corpus=corpus, wl=key[2], item=key[3], call=key[4],
               text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key] = rec
    return text


def run(alias, corpus):
    items = load_items(corpus)
    cache = load_cache()
    for wl in BUDGETS:
        for it in items:
            iid = it["id"]
            summary = api(alias, corpus, [{"role": "system", "content": comp_sys(wl)},
                                          {"role": "user", "content": it["document"]}],
                          cache, (alias, corpus, wl, iid, "compress"))
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(alias, corpus, [{"role": "user", "content": notes + ANS_SUFFIX}],
                cache, (alias, corpus, wl, iid, "decision"))
            api(alias, corpus, [{"role": "user", "content": notes + WHICH_PROBE}],
                cache, (alias, corpus, wl, iid, "which"))
        print(f"{alias}/{corpus} budget {wl} done ({len(cache)})", flush=True)


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx > 1e-12 else float("nan")
    intercept = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 1e-12 else float("nan")
    return slope, intercept, r2


def score():
    cache = load_cache()
    # include the cached grok/incident Phase B curve as the reference arm
    ref = {}
    curve_raw = os.path.join(HERE, "..", "..", "..", "witness-compaction", "2026-07-03",
                             "curve", "responses_raw.jsonl")
    for line in open(curve_raw):
        r = json.loads(line)
        ref[("grok", "incident", r["wl"], r["item"], r["call"])] = r

    arms = ARMS + [REFERENCE]
    corpora_items = {c: {it["id"]: it for it in load_items(c)} for c in CORPORA}
    rows, per_arm = [], {}
    for alias, corpus in arms:
        src = ref if (alias, corpus) == REFERENCE else cache
        items = corpora_items[corpus]
        curve = {}
        for wl in BUDGETS:
            sub = []
            for iid, it in items.items():
                r = src.get((alias, corpus, wl, iid, "compress"))
                if r is None:
                    continue
                summary = r["text"]
                pol = [p for p in it["parameters"] if p["policy"]]
                fail = next(p for p in pol if not p["passes"])
                dtxt = src.get((alias, corpus, wl, iid, "decision"), {}).get("text") or ""
                wtxt = src.get((alias, corpus, wl, iid, "which"), {}).get("text")
                m = ANS_RE.search(dtxt)
                wp, _ = parse_which(wtxt, it["parameters"])
                if wp in (None, "UNMATCHED") and corpus == "clinical":
                    # medical-abbreviation fallback, fixed before spend (clinical_match);
                    # was imported but unwired until 2026-07-06 — zero numerical effect,
                    # verified by re-scoring with and without (see README audit notes)
                    wp = resolve_which(wtxt, it["parameters"], it["failing_param"]) or wp
                row = dict(model=alias, corpus=corpus, wl=wl, item=iid,
                           realized_words=len(summary.split()),
                           fail_retained=retained(summary, fail["value"]),
                           decision_correct=(m.group(1).upper() if m else None) == "DENIED",
                           which_correct=wp == it["failing_param"])
                sub.append(row)
                rows.append(row)
            if not sub:
                continue
            n = len(sub)
            S = sum(r["fail_retained"] for r in sub) / n
            J = sum(r["which_correct"] for r in sub) / n
            curve[wl] = dict(n=n, S=S, J=J,
                             decision=sum(r["decision_correct"] for r in sub) / n,
                             realized_words=sum(r["realized_words"] for r in sub) / n,
                             eff_retained=frac_eff(sub, True), eff_lost=frac_eff(sub, False))
        if not curve:
            continue
        Ss = [curve[wl]["S"] for wl in BUDGETS if wl in curve]
        Js = [curve[wl]["J"] for wl in BUDGETS if wl in curve]
        max_gap = max(abs(curve[wl]["J"] - curve[wl]["S"]) for wl in curve)
        applicable = max(Ss) > 0.5
        slope, intercept, r2 = ols(Ss, Js)
        p_l1 = bool(max_gap <= 0.10)
        p_l2 = bool(applicable and 0.85 <= slope <= 1.15 and abs(intercept) <= 0.08 and r2 >= 0.90)
        per_arm[f"{alias}/{corpus}"] = dict(
            curve={str(k): v for k, v in curve.items()},
            max_gap=round(max_gap, 4), applicable_P_L2=applicable,
            slope=round(slope, 4), intercept=round(intercept, 4), r2=round(r2, 4),
            P_L1_pointwise=p_l1, P_L2_unitline=p_l2, law_holds=bool(p_l1 and p_l2))

    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # pooled regression across all confirmatory arms (exploratory)
    conf = [per_arm[f"{a}/{c}"] for a, c in ARMS if f"{a}/{c}" in per_arm]
    pooled_pts = [(v["S"], v["J"]) for a, c in ARMS if f"{a}/{c}" in per_arm
                  for v in per_arm[f"{a}/{c}"]["curve"].values()]
    ps, pj = [p[0] for p in pooled_pts], [p[1] for p in pooled_pts]
    pooled = dict(zip(("slope", "intercept", "r2"), [round(x, 4) for x in ols(ps, pj)]),
                  n_points=len(pooled_pts)) if pooled_pts else {}

    n_pass = sum(1 for a, c in ARMS if per_arm.get(f"{a}/{c}", {}).get("law_holds"))
    clin_pass = any(per_arm.get(f"{a}/{c}", {}).get("law_holds") for a, c in ARMS if c == "clinical")
    campaign = dict(arms_passing=n_pass, of=len(ARMS), clinical_pass=clin_pass,
                    law_survives=bool(n_pass >= 3 and clin_pass))

    tok = {}
    for r in cache.values():
        t = tok.setdefault(r["model"], dict(prompt=0, completion=0))
        t["prompt"] += r["usage"]["prompt"]
        t["completion"] += r["usage"]["completion"]
    cost = {a: round(cost_usd(a, tok[a]), 4) for a in tok}

    print(f"{'arm':16} {'gap':>6} {'slope':>7} {'icept':>7} {'r2':>6}  L1  L2  law")
    for a, c in arms:
        k = f"{a}/{c}"
        if k not in per_arm:
            continue
        v = per_arm[k]
        print(f"{k:16} {v['max_gap']:>6.3f} {v['slope']:>7.3f} {v['intercept']:>7.3f} "
              f"{v['r2']:>6.3f}  {'Y' if v['P_L1_pointwise'] else 'n'}   "
              f"{'Y' if v['P_L2_unitline'] else 'n'}   {'Y' if v['law_holds'] else 'n'}"
              f"{'' if v['applicable_P_L2'] else '  (P-L2 n/a: S<=0.5)'}")
    print(f"\npooled: slope={pooled.get('slope')} intercept={pooled.get('intercept')} "
          f"r2={pooled.get('r2')} (n={pooled.get('n_points')})")
    print(f"campaign: {campaign['arms_passing']}/{campaign['of']} arms hold, clinical={clin_pass} "
          f"-> LAW {'SURVIVES' if campaign['law_survives'] else 'DOES NOT SURVIVE'}")
    print(f"cost: {cost} total=${sum(cost.values()):.4f}")

    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(budgets=BUDGETS, arms=[f"{a}/{c}" for a, c in ARMS],
                                   reference="grok/incident (cached Phase B curve)",
                                   prereg="prereg_budgetline.md"),
                       per_arm=per_arm, pooled_regression=pooled, campaign=campaign,
                       tokens=tok, cost_usd=cost, total_cost_usd=round(sum(cost.values()), 4)),
                  f, indent=2)
    print(f"wrote {RESULTS}")


def frac_eff(sub, retained_cond):
    d = [r for r in sub if r["fail_retained"] == retained_cond]
    return (sum(r["which_correct"] for r in d) / len(d)) if d else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    ap.add_argument("--model", choices=["grok", "haiku", "gpt"])
    ap.add_argument("--corpus", choices=list(CORPORA))
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.model, a.corpus)
    else:
        score()


if __name__ == "__main__":
    main()
