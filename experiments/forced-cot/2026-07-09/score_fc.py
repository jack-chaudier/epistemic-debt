#!/usr/bin/env python3
"""Score the forced-CoT probe against the frozen prereg (P-FC-0..3). Local, no API.
Writes forced_cot_results.json. Frozen baselines (cached, distill-parity): GSM8K bare
sv 0.152 / sj 0.524 / base 0.516."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ANS_RE = re.compile(r"ANSWER\s*:\s*\**\s*([^\n*]+)", re.I)
BARE_GSM = dict(sv=0.152, sj=0.524, base=0.516)

cap = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "capability_items.jsonl")))}
abl = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "sections_items.jsonl")))}
raw = {}
for l in open(os.path.join(HERE, "responses_raw.jsonl")):
    r = json.loads(l)
    raw[(r["model"], r["item"], r["call"])] = r


def cap_score(m):
    accs, toks = {"gsm8k": [0, 0], "mmlu": [0, 0]}, []
    for it in cap.values():
        r = raw.get((m, it["id"], "cap_cot"))
        if r is None:
            continue
        if it["kind"] == "gsm8k":
            toks.append(r["usage"].get("completion_tokens", 0))
        mm = ANS_RE.findall(r["text"] or "")
        ok = False
        if mm:
            a = mm[-1].strip().rstrip(".").replace(",", "").replace("$", "")
            if it["kind"] == "gsm8k":
                try:
                    ok = abs(float(a.split()[0]) - float(it["gold"])) < 1e-6
                except (ValueError, IndexError):
                    ok = False
            else:
                ok = a[:1].upper() == it["gold"]
        accs[it["kind"]][0] += ok
        accs[it["kind"]][1] += 1
    toks.sort()
    return dict(gsm8k=round(accs["gsm8k"][0] / max(accs["gsm8k"][1], 1), 4),
                mmlu=round(accs["mmlu"][0] / max(accs["mmlu"][1], 1), 4),
                gsm8k_median_tokens=(toks[len(toks) // 2] if toks else None))


def abl_rates(m, call):
    a = ie = n_anch = tot = 0
    for it in abl.values():
        r = raw.get((m, it["id"], call))
        if r is None:
            continue
        tot += 1
        mm = ANS_RE.findall(r["text"] or "")
        v = mm[-1].strip().rstrip(".").upper().replace(" ", "_") if mm else None
        if v and "INSUFFICIENT" in v:
            ie += 1
        elif v in ("APPROVED", "DENIED"):
            n_anch += 1
            a += (v == "APPROVED")
    return dict(n=tot, approve=(round(a / n_anch, 4) if n_anch else None),
                anchored=n_anch, abstain=round(ie / tot, 4) if tot else None,
                unanchored=round((tot - n_anch - ie) / tot, 4) if tot else None)


out = dict(models={}, predictions={})
for m in ("sv", "sj", "base"):
    out["models"][m] = dict(
        cap_cot=cap_score(m), gsm8k_bare_frozen=BARE_GSM[m],
        abl_bare=abl_rates(m, "abl_bare"), abl_cot=abl_rates(m, "abl_cot"),
        abl_abstain=abl_rates(m, "abl_abstain"))

sv = out["models"]["sv"]
out["predictions"]["P-FC-0"] = dict(
    median_tokens=sv["cap_cot"]["gsm8k_median_tokens"],
    passed=bool((sv["cap_cot"]["gsm8k_median_tokens"] or 0) >= 60))
g = sv["cap_cot"]["gsm8k"]
out["predictions"]["P-FC-1"] = dict(
    sv_gsm8k_cot=g, threshold_latent=0.387, threshold_damaged=0.25,
    verdict=("LATENT" if g >= 0.387 else "DAMAGED" if g <= 0.25 else "PARTIAL"))
drop = ((sv["abl_bare"]["approve"] or 0) - (sv["abl_cot"]["approve"] or 0)
        if sv["abl_bare"]["approve"] is not None and sv["abl_cot"]["approve"] is not None
        else None)
drop_j = ((out["models"]["sj"]["abl_bare"]["approve"] or 0)
          - (out["models"]["sj"]["abl_cot"]["approve"] or 0))
out["predictions"]["P-FC-2"] = dict(sv_approve_drop=(round(drop, 4) if drop is not None else None),
                                    sj_approve_drop=round(drop_j, 4),
                                    passed=bool(drop is not None and drop >= 0.25))
out["predictions"]["P-FC-3"] = dict(
    sj_abstain=out["models"]["sj"]["abl_abstain"]["abstain"],
    sv_abstain=sv["abl_abstain"]["abstain"],
    passed_sj=bool((out["models"]["sj"]["abl_abstain"]["abstain"] or 0) >= 0.50),
    passed_sv=bool(sv["abl_abstain"]["abstain"] is not None
                   and sv["abl_abstain"]["abstain"] <= 0.20))
json.dump(out, open(os.path.join(HERE, "forced_cot_results.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
