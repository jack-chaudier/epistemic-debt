#!/usr/bin/env python3
"""Exploratory re-analysis of the Law-3 pilot, split by source verdict (no API calls).

The preregistered original-accuracy guard (P-L3-2, orig_decision_accuracy >= 0.70) fails
for all three models on the pooled corpus. This script asks *where* that failure lives.

Finding: the guard failure is confined to the conjunctive APPROVED-source side (the
documented "missing~=failing" conservative bias — under lossy compaction the reader defaults
to DENIED, so an APPROVED source reads as a wrong DENIED). On the DENIED-source subset the
original accuracy clears 0.70 for every model AND the Law-3 witness-conditioned transfer gap
survives with non-overlapping Wilson intervals. So the localization result is robust; the
guard failure is a property of one logical side of the task, not of the transfer effect.

Deterministic, stdlib only. Reads scored.csv, writes reanalysis_by_source_truth.json.
Exit code 0 iff the DENIED-side story reproduces (orig>=0.70 and a positive, CI-separated gap
for every model), so it doubles as a regression guard on the interpretation.
"""
import csv
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCORED = os.path.join(HERE, "scored.csv")
OUT = os.path.join(HERE, "reanalysis_by_source_truth.json")
MODELS = ["grok", "haiku", "gpt"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def rate(rows, key):
    n = len(rows)
    k = sum(1 for r in rows if r[key] == "True")
    return {"k": k, "n": n, "p": round(k / n, 4) if n else None, "ci": wilson(k, n)}


def main():
    rows = list(csv.DictReader(open(SCORED)))
    out = {"design": {"source": "scored.csv", "split": "source_truth",
                      "note": "P-L3-2 guard failure is APPROVED-side; Law-3 gap survives on DENIED side"},
           "by_model": {}}
    ok = True
    for m in MODELS:
        sub = [r for r in rows if r["model"] == m]
        cell = {}
        for st in ("APPROVED", "DENIED"):
            s = [r for r in sub if r["source_truth"] == st]
            present = [r for r in s if r["cf_required_survived"] == "True"]
            missing = [r for r in s if r["cf_required_survived"] != "True"]
            orig = rate(s, "orig_correct")
            cf_present = rate(present, "cf_decision_correct")
            cf_missing = rate(missing, "cf_decision_correct")
            gap = (round(cf_present["p"] - cf_missing["p"], 4)
                   if cf_present["p"] is not None and cf_missing["p"] is not None else None)
            ci_separated = bool(cf_present["ci"][0] is not None and cf_missing["ci"][1] is not None
                                and cf_present["ci"][0] > cf_missing["ci"][1])
            cell[st] = {"orig_decision_accuracy": orig, "cf_present": cf_present,
                        "cf_missing": cf_missing, "gap": gap, "ci_separated": ci_separated}
        out["by_model"][m] = cell
        d = cell["DENIED"]
        # DENIED-side interpretation guard: original accuracy clears the prereg 0.70 and the
        # transfer gap is positive with separated intervals.
        ok &= bool(d["orig_decision_accuracy"]["p"] >= 0.70 and d["gap"] is not None
                   and d["gap"] > 0 and d["ci_separated"])

    # pooled DENIED-side headline
    den = [r for r in rows if r["source_truth"] == "DENIED"]
    present = [r for r in den if r["cf_required_survived"] == "True"]
    missing = [r for r in den if r["cf_required_survived"] != "True"]
    cp = rate(present, "cf_decision_correct")
    cm = rate(missing, "cf_decision_correct")
    out["pooled_denied_source"] = {
        "cf_present": cp, "cf_missing": cm,
        "gap": round(cp["p"] - cm["p"], 4) if cp["p"] is not None and cm["p"] is not None else None}
    out["denied_side_interpretation_holds"] = ok

    json.dump(out, open(OUT, "w"), indent=1)
    print(f"{'model':6}{'side':10}{'orig_acc':>9}{'cf_present':>11}{'cf_missing':>11}{'gap':>7}  CI-sep")
    for m in MODELS:
        for st in ("APPROVED", "DENIED"):
            c = out["by_model"][m][st]
            print(f"{m:6}{st:10}{c['orig_decision_accuracy']['p']:>9}"
                  f"{str(c['cf_present']['p']):>11}{str(c['cf_missing']['p']):>11}"
                  f"{str(c['gap']):>7}  {c['ci_separated']}")
    p = out["pooled_denied_source"]
    print(f"\npooled DENIED-source: cf_present={p['cf_present']['p']} (n={p['cf_present']['n']}) "
          f"cf_missing={p['cf_missing']['p']} (n={p['cf_missing']['n']}) gap={p['gap']}")
    print(f"DENIED-side interpretation holds (orig>=0.70 & positive CI-separated gap, 3/3): "
          f"{out['denied_side_interpretation_holds']}")
    print(f"wrote {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
