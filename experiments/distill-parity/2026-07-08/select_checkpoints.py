#!/usr/bin/env python3
"""Frozen checkpoint-selection rule (prereg d24e198): over the 3x2 epoch-end checkpoints,
evaluated on the 300-item dev slice, choose the (V, J) pair minimizing |acc_V - acc_J| subject
to both >= 0.70 on EACH verdict side of the dev slice; ties break toward the later epoch.
The dev slice never appears in any reported number.

Reads responses_raw.jsonl (dev battery, models sv1..sv3 / sj1..sj3), writes
checkpoint_selection.json. Exit 3 if no pair satisfies the constraint (P-DP-0 heading to VOID).
"""
import itertools
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ANS_LAST_RE = re.compile(r"ANSWER\s*:\s*\**\s*(APPROVED|DENIED)", re.I)

items = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "dev_slice.jsonl")))}
resp = {}
for line in open(os.path.join(HERE, "responses_raw.jsonl")):
    r = json.loads(line)
    if r["call"] == "decision" and r["item"] in items:
        resp[(r["model"], r["item"])] = r["text"]


def parse(text):
    m = ANS_LAST_RE.findall(text or "")
    if m:
        return m[-1].upper()
    m = re.findall(r"\b(APPROVED|DENIED)\b", text or "", re.I)
    return m[-1].upper() if m else None


def side_acc(model):
    out = {}
    for side in ("APPROVED", "DENIED"):
        sub = [it for it in items.values() if it["truth"] == side]
        got = [parse(resp.get((model, it["id"]))) for it in sub]
        out[side] = round(sum(g == side for g in got) / len(sub), 4)
    out["overall"] = round(sum(parse(resp.get((model, it["id"]))) == it["truth"]
                               for it in items.values()) / len(items), 4)
    return out


V = {f"sv{k}": side_acc(f"sv{k}") for k in (1, 2, 3)}
J = {f"sj{k}": side_acc(f"sj{k}") for k in (1, 2, 3)}
ok_v = [m for m in V if V[m]["APPROVED"] >= 0.70 and V[m]["DENIED"] >= 0.70]
ok_j = [m for m in J if J[m]["APPROVED"] >= 0.70 and J[m]["DENIED"] >= 0.70]
pairs = [(a, b) for a, b in itertools.product(ok_v, ok_j)]
result = dict(dev_acc_V=V, dev_acc_J=J, eligible_V=ok_v, eligible_J=ok_j)
if not pairs:
    result["selected"] = None
    json.dump(result, open(os.path.join(HERE, "checkpoint_selection.json"), "w"), indent=1)
    print(json.dumps(result, indent=1))
    print("NO ELIGIBLE PAIR — P-DP-0 heading to VOID", file=sys.stderr)
    sys.exit(3)
# minimize |acc_V - acc_J| on overall dev accuracy; ties -> later epochs (higher indices)
best = min(pairs, key=lambda p: (abs(V[p[0]]["overall"] - J[p[1]]["overall"]),
                                 -(int(p[0][-1]) + int(p[1][-1]))))
result["selected"] = dict(V=best[0], J=best[1],
                          gap=round(abs(V[best[0]]["overall"] - J[best[1]]["overall"]), 4))
json.dump(result, open(os.path.join(HERE, "checkpoint_selection.json"), "w"), indent=1)
print(json.dumps(result, indent=1))
