#!/usr/bin/env python3
"""Score the budget-line (J=S) under BOTH the preregistered parser and the corrected one.

The prereg fixed `parse_which` (v3), which the 2026-07-06 re-score showed mis-parses verbose
readers' WHICH responses (first-match/optional-colon → UNMATCHED). That depresses J for haiku
in particular, and J=S is a claim about the *reader*, so a parser bug is a direct confound.
This reports P-L1 / P-L2 per arm under v1 (prereg) and v2 (corrected: last PARAMETER: match,
colon required) so the law's verdict is separated from the measurement artifact. No API calls.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03"))
from runner3 import retained, parse_which, match_param, ANS_RE
from clinical_match import resolve_which

CORPORA = {
    "incident": os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03", "v5", "items.jsonl"),
    "clinical": os.path.join(HERE, "items_clinical.jsonl"),
}
CURVE = os.path.join(HERE, "..", "..", "..", "witness-compaction", "2026-07-03", "curve",
                     "responses_raw.jsonl")
BUDGETS = [5, 10, 15, 25, 40, 60, 80]
ARMS = [("grok", "incident"), ("haiku", "incident"), ("gpt", "incident"),
        ("grok", "clinical"), ("gpt", "clinical")]
PARAM_COLON_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)


def parse_which_v2(text, params):
    m = PARAM_COLON_RE.findall(text or "")
    if not m:
        return None
    raw = m[-1].strip().rstrip(".")
    up = raw.upper().replace(" ", "_")
    if "INSUFFICIENT" in up:
        return "INSUFFICIENT_EVIDENCE"
    if up.startswith("NONE"):
        return "NONE"
    return match_param(raw, params) or "UNMATCHED"


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx if sxx > 1e-12 else float("nan")
    icept = my - slope * mx
    sst = sum((y - my) ** 2 for y in ys)
    ssr = sum((y - (slope * x + icept)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ssr / sst if sst > 1e-12 else float("nan")
    return slope, icept, r2


def load_arm(alias, corpus):
    if (alias, corpus) == ("grok", "incident"):
        src = {}
        for line in open(CURVE):
            r = json.loads(line)
            src[(alias, corpus, r["wl"], r["item"], r["call"])] = r
        return src
    src = {}
    raw = os.path.join(HERE, "responses_raw.jsonl")
    if os.path.exists(raw):
        for line in open(raw):
            r = json.loads(line)
            src[(r["model"], r["corpus"], r["wl"], r["item"], r["call"])] = r
    return src


def curve_for(alias, corpus, parser):
    items = {it["id"]: it for it in map(json.loads, open(CORPORA[corpus]))
             if it["truth"] == "DENIED"}
    src = load_arm(alias, corpus)
    out = {}
    for wl in BUDGETS:
        S = Jn = n = 0
        for iid, it in items.items():
            r = src.get((alias, corpus, wl, iid, "compress"))
            if r is None:
                continue
            n += 1
            s = r["text"]
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next(p for p in pol if not p["passes"])
            S += retained(s, fail["value"])
            wtxt = src.get((alias, corpus, wl, iid, "which"), {}).get("text")
            if parser == "v1":
                wp, _ = parse_which(wtxt, it["parameters"])
            else:
                wp = parse_which_v2(wtxt, it["parameters"])
            # clinical shorthand resolution applies to both parsers (prereg scoring aid)
            if wp in (None, "UNMATCHED") and corpus == "clinical":
                rw = resolve_which(wtxt, it["parameters"], it["failing_param"])
                Jn += rw == it["failing_param"]
            else:
                Jn += wp == it["failing_param"]
        if n:
            out[wl] = (S / n, Jn / n, n)
    return out


def verdict(curve):
    Ss = [curve[wl][0] for wl in BUDGETS if wl in curve]
    Js = [curve[wl][1] for wl in BUDGETS if wl in curve]
    if len(Ss) < 3:
        return None
    max_gap = max(abs(curve[wl][1] - curve[wl][0]) for wl in curve)
    applicable = max(Ss) > 0.5
    slope, icept, r2 = ols(Ss, Js)
    p_l1 = max_gap <= 0.10
    p_l2 = applicable and 0.85 <= slope <= 1.15 and abs(icept) <= 0.08 and r2 >= 0.90
    return dict(max_gap=round(max_gap, 4), slope=round(slope, 4), intercept=round(icept, 4),
                r2=round(r2, 4), applicable=applicable, P_L1=p_l1, P_L2=p_l2,
                law=p_l1 and p_l2, n_budgets=len(Ss))


def main():
    out = {}
    for parser in ("v1", "v2"):
        print(f"\n=== parser {parser} ({'prereg' if parser=='v1' else 'corrected'}) ===")
        print(f"{'arm':16}{'gap':>7}{'slope':>7}{'icept':>7}{'r2':>7}  L1 L2 law")
        npass = clin = 0
        for a, c in ARMS:
            cur = curve_for(a, c, parser)
            v = verdict(cur)
            out[f"{parser}/{a}/{c}"] = dict(curve={str(k): cur[k] for k in cur}, verdict=v)
            if v is None:
                print(f"{a+'/'+c:16}  (incomplete: {len(cur)} budgets)")
                continue
            if (a, c) != ("grok", "incident") and v["law"]:
                npass += 1
                clin |= c == "clinical"
            tag = "" if v["applicable"] else "  (P-L2 n/a S<=.5)"
            print(f"{a+'/'+c:16}{v['max_gap']:>7.3f}{v['slope']:>7.3f}{v['intercept']:>7.3f}"
                  f"{v['r2']:>7.3f}  {'Y' if v['P_L1'] else 'n'}  {'Y' if v['P_L2'] else 'n'}  "
                  f"{'Y' if v['law'] else 'n'}{tag}")
        survives = npass >= 3 and clin
        out[f"{parser}/campaign"] = dict(arms_passing=npass, clinical_pass=bool(clin),
                                         law_survives=bool(survives))
        print(f"campaign ({parser}): {npass}/4 confirmatory arms hold, clinical={bool(clin)} "
              f"-> LAW {'SURVIVES' if survives else 'DOES NOT SURVIVE'}")
    json.dump(out, open(os.path.join(HERE, "dualparser_results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
