#!/usr/bin/env python3
"""Budget-compliance control + path-ensemble ceiling for the recursive phase (no API).

Both arms of the rolling-compaction experiment violate the nominal 15-word terminal budget
(realized >15w: chain 11/30, direct 14/30; gross >25w: 7/30 each), and the chain's rescued
items are among the violators — so the headline "chain ≈ direct" needs a compliance-conditioned
check. Also computes the path-diversity union: how many witnesses survive in at least one of
the two artifacts.
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "..", "witness-compaction", "2026-07-03", "recursive", "scored.csv")


def main():
    rows = list(csv.DictReader(open(REC)))
    ch = {r["item"]: r for r in rows if r["arm"] == "chain"}
    dr = {r["item"]: r for r in rows if r["arm"] == "direct"}
    items = sorted(set(ch) & set(dr))
    f = lambda r, k: float(r[k])
    out = {}

    def stats(sub, tag):
        n = len(sub)
        d = dict(n=n)
        if n:
            d.update(chain_ret=round(sum(f(ch[i], "ret_policy") for i in sub) / n, 4),
                     direct_ret=round(sum(f(dr[i], "ret_policy") for i in sub) / n, 4),
                     chain_which=sum(ch[i]["which_correct"] == "True" for i in sub),
                     direct_which=sum(dr[i]["which_correct"] == "True" for i in sub))
        out[tag] = d
        print(tag, d)

    stats(items, "all")
    for cap in (20, 25):
        stats([i for i in items if f(ch[i], "words") <= cap and f(dr[i], "words") <= cap],
              f"both_final_le_{cap}w")
    out["overshoot"] = dict(
        chain=sorted((i, int(f(ch[i], "words"))) for i in items if f(ch[i], "words") > 25),
        direct=sorted((i, int(f(dr[i], "words"))) for i in items if f(dr[i], "words") > 25))
    chw = {i for i in items if ch[i]["which_correct"] == "True"}
    drw = {i for i in items if dr[i]["which_correct"] == "True"}
    chr_ = {i for i in items if ch[i]["fail_retained"] == "True"}
    drr = {i for i in items if dr[i]["fail_retained"] == "True"}
    out["path_ensemble"] = dict(
        which_chain=len(chw), which_direct=len(drw),
        which_union=len(chw | drw), which_intersection=len(chw & drw),
        retained_chain=len(chr_), retained_direct=len(drr), retained_union=len(chr_ | drr),
        n=len(items))
    print("path_ensemble", out["path_ensemble"])
    json.dump(out, open(os.path.join(HERE, "recursive_reanalysis.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
