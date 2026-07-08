#!/usr/bin/env python3
"""Score a J-prompt revision probe against the frozen threshold (revision_protocol.md rule 3).

Joint-survival = full G3 conjunction: cached bare-ANSWER verdict correct (teacher_raw.jsonl,
V prompt unchanged) AND revised-J verdict correct (probe_j_raw.jsonl, last-DECISION-anchor
parser) AND named deciding witness correct. Reports DENIED and APPROVED survival; the
proceed threshold is DENIED >= 0.55. Writes probe_results.json. Exit 0 always (reported gate)."""
import json
import os

from trace_builder import parse_verdict, parse_j_verdict_r1, j_witness_ok

HERE = os.path.dirname(os.path.abspath(__file__))

items = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "probe_slice.jsonl")))}
v_txt = {}
for line in open(os.path.join(HERE, "teacher_raw.jsonl")):
    r = json.loads(line)
    if r["call"] == "teacher_v" and r["item"] in items:
        v_txt[r["item"]] = r["text"]
j_txt = {}
for line in open(os.path.join(HERE, "probe_j_raw.jsonl")):
    r = json.loads(line)
    if r["call"] == "teacher_j":
        j_txt[r["item"]] = r["text"]

out = {}
for side in ("DENIED", "APPROVED"):
    sub = [it for it in items.values() if it["truth"] == side]
    n = len(sub)
    v_ok = sum(parse_verdict(v_txt[it["id"]]) == side for it in sub)
    jv_ok = sum(parse_j_verdict_r1(j_txt[it["id"]]) == side for it in sub)
    joint = sum((parse_verdict(v_txt[it["id"]]) == side)
                and (parse_j_verdict_r1(j_txt[it["id"]]) == side)
                and j_witness_ok(it, j_txt[it["id"]]) for it in sub)
    out[side] = dict(n=n, v_ok=round(v_ok / n, 4), j_verdict_ok=round(jv_ok / n, 4),
                     joint_survival=round(joint / n, 4))
out["threshold"] = dict(metric="DENIED joint_survival", value=0.55,
                        passed=out["DENIED"]["joint_survival"] >= 0.55)
json.dump(out, open(os.path.join(HERE, "probe_results.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
