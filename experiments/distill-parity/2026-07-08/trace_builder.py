#!/usr/bin/env python3
"""Build the two SFT trace sets from the teacher's raw outputs, applying gates G2/G3/G4.

Input:  train_pool.jsonl + teacher_raw.jsonl (pod-generated; records
        {model,item,call in {teacher_v, teacher_j}, text, usage}, think-blocks pre-stripped).
Output: train_V.jsonl / train_J.jsonl (messages format) + gate_manifest.json.

Gates (FROZEN, prereg d24e198):
  G2  per corpus: teacher full-document verdict accuracy (from the teacher_v channel) >= 0.85;
      corpora below the gate are dropped entirely. STOP condition if > 2 of 6 drop.
  G3  joint filter -> ONE shared item set: an item survives iff
        - teacher_v verdict correct, AND
        - teacher_j verdict correct, AND
        - the J-trace's named deciding witness is correct against ground truth:
            DENIED item:   last PARAMETER: anchor matches failing_param AND the failing
                           value string is retained() in the trace;
            APPROVED item: no failing parameter is claimed (PARAMETER: NONE or no anchor)
                           AND all three policy values are retained() in the trace.
      (Implementation note, not reinterpretation: for APPROVED items "the deciding witness"
      is the full passing triple, since no single reading decides an approval.)
      STOP condition if < 3000 items survive.
  G4  50/50 APPROVED/DENIED downsample (seeded, per prereg) applied to the shared set.

Both conditions are built from the SAME post-G4 item list:
  V example: user = policy + document + bare decision request; assistant = teacher_v text.
  J example: user = policy + document + fusion-register request; assistant = teacher_j text.
The request wording is part of the manipulated trace-content package (disclosed in PLAN.md).
Teacher text is used verbatim (distillation), not re-templated.
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained, match_param, ANS_RE  # noqa: E402

G4_SEED = 812950
PARAM_COLON_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)

# Prompt suffixes — MUST stay byte-identical to runner.py's TEACHER_V / TEACHER_J.
V_REQ = (" Was the decision APPROVED or DENIED per policy? "
         "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
J_REQ = (" State the decision and its justification in the fusion register: one clause that "
         "names the verdict together with the deciding reading(s) and threshold(s) — never a "
         "verdict without its deciding value in the same clause. Then on a new line reply "
         "exactly: PARAMETER: <failing parameter name> if DENIED, or PARAMETER: NONE if "
         "APPROVED. If a needed reading is absent, say [MISSING DATA] and name what is missing.")


def user_content(item, req):
    return (item["policy_text"] + "\n\nCase file:\n" + item["document"] + "\n\n" + req.strip())


def parse_verdict(text):
    m = ANS_RE.search(text or "")
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(APPROVED|DENIED)\b", text or "", re.I)
    return m.group(1).upper() if m else None


def j_witness_ok(item, jtext):
    anchors = PARAM_COLON_RE.findall(jtext or "")
    named = anchors[-1].strip().rstrip(".") if anchors else None
    pol = [p for p in item["parameters"] if p["policy"]]
    if item["truth"] == "DENIED":
        fail = next(p for p in pol if not p["passes"])
        return (named is not None
                and match_param(named, item["parameters"]) == item["failing_param"]
                and retained(jtext, fail["value"]))
    claims_fail = (named is not None and not named.upper().startswith("NONE"))
    return (not claims_fail) and all(retained(jtext, p["value"]) for p in pol)


def main():
    items = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "train_pool.jsonl")))}
    v_txt, j_txt = {}, {}
    for line in open(os.path.join(HERE, "teacher_raw.jsonl")):
        r = json.loads(line)
        if r["call"] == "teacher_v":
            v_txt[r["item"]] = r["text"]
        elif r["call"] == "teacher_j":
            j_txt[r["item"]] = r["text"]

    domains = sorted({it["domain"] for it in items.values()})
    manifest = dict(g2={}, g2_dropped=[], g3={}, g4={})
    # G2
    kept_domains = []
    for d in domains:
        ditems = [it for it in items.values() if it["domain"] == d and it["id"] in v_txt]
        correct = sum(parse_verdict(v_txt[it["id"]]) == it["truth"] for it in ditems)
        acc = correct / len(ditems) if ditems else 0.0
        manifest["g2"][d] = dict(n=len(ditems), teacher_v_acc=round(acc, 4))
        (kept_domains if acc >= 0.85 else manifest["g2_dropped"]).append(d)
    # G3
    survivors = []
    tallies = dict(total=0, missing_calls=0, v_wrong=0, j_verdict_wrong=0, j_witness_wrong=0)
    for it in items.values():
        if it["domain"] not in kept_domains:
            continue
        tallies["total"] += 1
        iid = it["id"]
        if iid not in v_txt or iid not in j_txt:
            tallies["missing_calls"] += 1
            continue
        if parse_verdict(v_txt[iid]) != it["truth"]:
            tallies["v_wrong"] += 1
            continue
        if parse_verdict(j_txt[iid]) != it["truth"]:
            tallies["j_verdict_wrong"] += 1
            continue
        if not j_witness_ok(it, j_txt[iid]):
            tallies["j_witness_wrong"] += 1
            continue
        survivors.append(it)
    manifest["g3"] = dict(tallies, survivors=len(survivors))
    # G4
    rng = random.Random(G4_SEED)
    app = [it for it in survivors if it["truth"] == "APPROVED"]
    den = [it for it in survivors if it["truth"] == "DENIED"]
    k = min(len(app), len(den))
    rng.shuffle(app), rng.shuffle(den)
    final = app[:k] + den[:k]
    rng.shuffle(final)
    manifest["g4"] = dict(approved=len(app), denied=len(den), per_side=k, final=2 * k)

    for name, req, txt in (("train_V.jsonl", V_REQ, v_txt), ("train_J.jsonl", J_REQ, j_txt)):
        with open(os.path.join(HERE, name), "w") as f:
            for it in final:
                f.write(json.dumps(dict(messages=[
                    dict(role="user", content=user_content(it, req)),
                    dict(role="assistant", content=txt[it["id"]].strip())])) + "\n")
    json.dump(manifest, open(os.path.join(HERE, "gate_manifest.json"), "w"), indent=1)
    print(json.dumps(manifest, indent=1))
    if len(manifest["g2_dropped"]) > 2:
        print("STOP CONDITION: G2 dropped >2 corpora", file=sys.stderr)
        sys.exit(3)
    if 2 * k < 3000:
        print("STOP CONDITION: G3/G4 final set <3000 items", file=sys.stderr)
        sys.exit(3)
    print(f"wrote train_V.jsonl / train_J.jsonl with {2 * k} examples each")


if __name__ == "__main__":
    main()
