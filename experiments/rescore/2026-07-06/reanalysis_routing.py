#!/usr/bin/env python3
"""Router-design comparison on the cached routing corpus (no API calls). See README.md.

Compares, on grok's 30 DENIED v5 items:
  A. abstention router (as run in witness-compaction/routing)
  B. A + incoherence trigger (verdict DENIED while WHICH says NONE)
  C. simulated loss-ledger router: route iff any policy value is absent from the
     artifact by string check. Deployable contract-blind: the compactor logs the
     *names* of values it dropped; at read time the router intersects the ledger
     with the parameters named in the query's policy. No model call, recall 1.0
     by construction.
  D. B + C union (equals C on this corpus).

End-to-end scoring mirrors the routing phase: routed items score full-document
WHICH (cached full_correct); unrouted items score notes-side WHICH.
"""
import csv, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, "..", "..", "multimodel", "2026-07-03", "v5", "scored.csv")
RT = os.path.join(HERE, "..", "..", "witness-compaction", "2026-07-03", "routing", "scored.csv")


def main():
    v5 = [r for r in csv.DictReader(open(V5)) if r["model"] == "grok" and r["truth"] == "DENIED"]
    rt = {r["item"]: r for r in csv.DictReader(open(RT))}
    lost = [r for r in v5 if r["fail_retained"] == "False"]

    designs = {
        "A_abstention": lambda r: r["abstained"] == "True",
        "B_plus_incoherence": lambda r: r["abstained"] == "True" or
                                        (r["decision"] == "DENIED" and r["which"] == "NONE"),
        "C_ledger_sim": lambda r: r["any_policy_lost"] == "True",
        "D_union": lambda r: r["abstained"] == "True" or
                             (r["decision"] == "DENIED" and r["which"] == "NONE") or
                             r["any_policy_lost"] == "True",
    }
    out = {}
    for name, fires in designs.items():
        fired = [r for r in v5 if fires(r)]
        tp = sum(1 for r in fired if r["fail_retained"] == "False")
        e2e = 0
        for r in v5:
            rr = rt.get(r["item"])
            if fires(r):
                e2e += (rr is None or rr["full_correct"] == "True")
            else:
                e2e += (rr["notes_correct"] == "True") if rr else (r["which_correct"] == "True")
        out[name] = dict(fires=len(fired), n=len(v5), recall=round(tp / len(lost), 4),
                         precision=round(tp / len(fired), 4) if fired else None,
                         end_to_end=f"{e2e}/{len(v5)}")
        print(f"{name:22s} fires={len(fired):2d}/30 recall={out[name]['recall']:.3f} "
              f"precision={out[name]['precision']:.3f} end-to-end={e2e}/30")
    json.dump(out, open(os.path.join(HERE, "routing_reanalysis.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
