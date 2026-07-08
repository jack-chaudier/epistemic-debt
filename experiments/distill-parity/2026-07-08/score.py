#!/usr/bin/env python3
"""Distill-parity scorer: raw responses -> per-battery metrics -> P-DP-* pass/fail
(frozen prereg d24e198) -> distill_parity_results.json.

    python3 score.py --teacher "Qwen/Qwen3-8B" --sv svN --sj sjN

Parsers: last-anchor everywhere (confound-checklist #2); UNMATCHED and anomaly counts are
surfaced per cell, never silently binned. Wilson 95% CIs. Δ note: delta-battery cells are
DENIED items split by witness survival, so the prereg's "calibrated" lost-cell target
(conservative DENIED) coincides with truth-correctness there; Δ is reported once, with that
identity stated. Arm 3a additionally carries the pre-committed compliance diagnostic
(arm3a_compliance_diagnostic.md): bare-compliance rate + accuracy split bare-only vs preamble.
"""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained, match_param  # noqa: E402

ANS_LAST_RE = re.compile(r"ANSWER\s*:\s*\**\s*(APPROVED|DENIED)", re.I)
PARAM_COLON_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)
MISSING_RE = re.compile(r"not (?:present|provided|include|available|contain|specified|given|listed|mention)"
                        r"|missing|absent|no (?:reading|value|measurement|data|information)|"
                        r"cannot (?:determine|verify|confirm)|insufficient|not enough", re.I)
BARE_RE = re.compile(r"^\s*ANSWER\s*:\s*(APPROVED|DENIED)\.?\s*$", re.I)
CAP_ANS_RE = re.compile(r"ANSWER\s*:\s*\**\s*([^\n*]+)", re.I)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def cell(k, n):
    return dict(k=k, n=n, p=(round(k / n, 4) if n else None), ci=wilson(k, n))


def parse_decision(text):
    m = ANS_LAST_RE.findall(text or "")
    if m:
        return m[-1].upper()
    m = re.findall(r"\b(APPROVED|DENIED)\b", text or "", re.I)
    return m[-1].upper() if m else None


def parse_which(text, params):
    m = PARAM_COLON_RE.findall(text or "")
    if not m:
        return None, None
    raw = m[-1].strip().rstrip(".")
    up = raw.upper().replace(" ", "_")
    if "INSUFFICIENT" in up:
        return "INSUFFICIENT_EVIDENCE", raw
    if up.startswith("NONE"):
        return "NONE", raw
    return match_param(raw, params) or "UNMATCHED", raw


def load_items(name, path=None):
    p = path or os.path.join(HERE, name)
    return [json.loads(l) for l in open(p)]


def load_raw():
    raw = {}
    for line in open(os.path.join(HERE, "responses_raw.jsonl")):
        r = json.loads(line)
        raw[(r["model"], r["item"], r["call"])] = r["text"]
    return raw


def decision_battery(raw, model, items):
    out = {}
    unmatched = 0
    for side in ("APPROVED", "DENIED"):
        sub = [it for it in items if it["truth"] == side]
        k = 0
        for it in sub:
            d = parse_decision(raw.get((model, it["id"], "decision")))
            if d is None:
                unmatched += 1
            k += d == side
        out[side] = cell(k, len(sub))
    out["overall"] = cell(sum(out[s]["k"] for s in ("APPROVED", "DENIED")), len(items))
    out["unmatched"] = unmatched
    return out


def capability_battery(raw, model, items):
    res = dict(gsm8k=dict(k=0, n=0), mmlu=dict(k=0, n=0), unmatched=0)
    for it in items:
        t = raw.get((model, it["id"], "cap_answer"))
        m = CAP_ANS_RE.findall(t or "")
        res[it["kind"]]["n"] += 1
        if not m:
            res["unmatched"] += 1
            continue
        ans = m[-1].strip().rstrip(".").replace(",", "")
        gold = it["gold"]
        if it["kind"] == "gsm8k":
            try:
                ok = abs(float(ans.split()[0]) - float(gold)) < 1e-6
            except (ValueError, IndexError):
                ok = False
        else:
            ok = ans[:1].upper() == gold
        res[it["kind"]]["k"] += ok
    for kind in ("gsm8k", "mmlu"):
        res[kind] = cell(res[kind]["k"], res[kind]["n"])
    res["overall"] = cell(res["gsm8k"]["k"] + res["mmlu"]["k"], len(items))
    return res


def delta_battery(raw, model, items):
    rows = []
    for it in items:
        summary = raw.get((model, it["id"], "compress"))
        if summary is None:
            continue
        pol = [p for p in it["parameters"] if p["policy"]]
        fail = next((p for p in pol if not p["passes"]), None)
        d = parse_decision(raw.get((model, it["id"], "decision")))
        wp, _ = parse_which(raw.get((model, it["id"], "which")), it["parameters"])
        ab, _ = parse_which(raw.get((model, it["id"], "which_abstain")), it["parameters"])
        rows.append(dict(
            truth=it["truth"], domain=it["domain"],
            fail_retained=(retained(summary, fail["value"]) if fail else None),
            decision_ok=(d == it["truth"]),
            which=wp, which_ok=(wp == (it["failing_param"] or "NONE")),
            incoherent=(d == "DENIED" and wp == "NONE"),
            none_missing=(wp == "NONE" and bool(MISSING_RE.search(raw.get((model, it["id"], "which")) or ""))),
            abstained=(ab == "INSUFFICIENT_EVIDENCE")))
    den = [r for r in rows if r["truth"] == "DENIED"]
    lost = [r for r in den if r["fail_retained"] is False]
    kept = [r for r in den if r["fail_retained"] is True]
    app = [r for r in rows if r["truth"] == "APPROVED"]

    def c(sub, key):
        return cell(sum(1 for r in sub if r[key]), len(sub))
    dl, dk = c(lost, "decision_ok"), c(kept, "decision_ok")
    out = dict(
        n_denied=len(den), n_lost=len(lost), n_kept=len(kept), n_approved=len(app),
        decision_lost=dl, decision_retained=dk,
        delta=(round(dk["p"] - dl["p"], 4) if dl["p"] is not None and dk["p"] is not None else None),
        which_lost=c(lost, "which_ok"), which_retained=c(kept, "which_ok"),
        incoherent_lost=c(lost, "incoherent"), abstain_lost=c(lost, "abstained"),
        abstain_retained=c(kept, "abstained"),
        unmatched_which=sum(1 for r in den if r["which"] == "UNMATCHED"),
        approved_decision=c(app, "decision_ok"),
        per_domain={d: dict(
            delta=(lambda L, K: round(K - L, 4) if L is not None and K is not None else None)(
                c([r for r in lost if r["domain"] == d], "decision_ok")["p"],
                c([r for r in kept if r["domain"] == d], "decision_ok")["p"]),
            n_lost=len([r for r in lost if r["domain"] == d]))
            for d in sorted({r["domain"] for r in rows})})
    return out


def arm3a_battery(raw, model, items):
    rows = []
    for it in items:
        t = raw.get((model, it["id"], "cf_decision"))
        d = parse_decision(t)
        rows.append(dict(ok=(d == it["cf_truth"]), bare=bool(BARE_RE.match(t or "")),
                         unmatched=(d is None), domain=it["domain"]))
    n = len(rows)
    err = sum(1 for r in rows if not r["ok"])
    bare = [r for r in rows if r["bare"]]
    pre = [r for r in rows if not r["bare"]]
    return dict(
        n=n, error=cell(err, n), unmatched=sum(r["unmatched"] for r in rows),
        bare_compliance=cell(len(bare), n),
        acc_bare_only=cell(sum(r["ok"] for r in bare), len(bare)),
        acc_preamble=cell(sum(r["ok"] for r in pre), len(pre)),
        per_domain={d: cell(sum(1 for r in rows if r["domain"] == d and not r["ok"]),
                            sum(1 for r in rows if r["domain"] == d))
                    for d in sorted({r["domain"] for r in rows})})


def arm3b_battery(raw, model, items):
    rows = []
    for it in items:
        summary = raw.get((model, it["id"], "compress_vd"))
        if summary is None:
            continue
        g = parse_decision(raw.get((model, it["id"], "guard_decision")))
        d = parse_decision(raw.get((model, it["id"], "cf_decision")))
        req = ([p for p in it["cf_parameters"] if not p["passes"]]
               if it["cf_truth"] == "DENIED" else it["cf_parameters"])
        present = all(retained(summary, p["value"]) for p in req)
        rows.append(dict(src_truth=it["truth"], guard_ok=(g == it["truth"]),
                         cf_ok=(d == it["cf_truth"]), present=present))
    guard = {s: cell(sum(r["guard_ok"] for r in rows if r["src_truth"] == s),
                     sum(1 for r in rows if r["src_truth"] == s))
             for s in ("APPROVED", "DENIED")}
    guard_pass = all(guard[s]["p"] is not None and guard[s]["p"] >= 0.70
                     for s in ("APPROVED", "DENIED"))
    absent = [r for r in rows if not r["present"]]
    present = [r for r in rows if r["present"]]
    return dict(
        n=len(rows), guard=guard, guard_pass_070_both_sides=guard_pass,
        witness_present_rate=round(len(present) / len(rows), 4) if rows else None,
        err_witness_absent=cell(sum(not r["cf_ok"] for r in absent), len(absent)),
        err_witness_present=cell(sum(not r["cf_ok"] for r in present), len(present)))


def ci_separated(a, b):
    """True iff a's CI lies strictly above b's (no overlap)."""
    return a["ci"][0] is not None and b["ci"][1] is not None and a["ci"][0] > b["ci"][1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", required=True)
    ap.add_argument("--sv", required=True)
    ap.add_argument("--sj", required=True)
    a = ap.parse_args()
    raw = load_raw()
    models = dict(teacher=a.teacher, V=a.sv, J=a.sj)
    parity_items = load_items("parity_gauge.jsonl")
    cap_items = (load_items("capability_items.jsonl")
                 if os.path.exists(os.path.join(HERE, "capability_items.jsonl")) else [])
    delta_items = load_items("delta_battery.jsonl")
    arm3_items = load_items("arm3.jsonl")
    rd_items = load_items(None, os.path.join(REPO, "experiments", "realdoc", "2026-07-08", "items.jsonl"))

    R = {}
    for tag, m in models.items():
        R[tag] = dict(
            parity=decision_battery(raw, m, parity_items),
            capability=(capability_battery(raw, m, cap_items) if cap_items else None),
            delta=delta_battery(raw, m, delta_items),
            arm3a=arm3a_battery(raw, m, arm3_items),
            arm3b=arm3b_battery(raw, m, arm3_items),
            realdoc=delta_battery(raw, m, rd_items))

    V, J, T = R["V"], R["J"], R["teacher"]
    preds = {}
    pv, pj = V["parity"], J["parity"]
    parity_gap = abs(pv["overall"]["p"] - pj["overall"]["p"])
    cap_gap = (abs(V["capability"]["overall"]["p"] - J["capability"]["overall"]["p"])
               if V["capability"] else None)
    preds["P-DP-0"] = dict(
        parity_gap=round(parity_gap, 4), cap_gap=(round(cap_gap, 4) if cap_gap is not None else None),
        sides_ok=all(x[s]["p"] >= 0.70 for x in (pv, pj) for s in ("APPROVED", "DENIED")),
        passed=bool(parity_gap <= 0.05
                    and all(x[s]["p"] >= 0.70 for x in (pv, pj) for s in ("APPROVED", "DENIED"))
                    and (cap_gap is None or cap_gap <= 0.05)))
    dsep = (V["delta"]["delta"] - J["delta"]["delta"]
            if V["delta"]["delta"] is not None and J["delta"]["delta"] is not None else None)
    # CI separation on the lost-cell decision accuracies (the moving part of Δ)
    preds["P-DP-1"] = dict(
        delta_V=V["delta"]["delta"], delta_J=J["delta"]["delta"], separation=dsep,
        ci_sep=ci_separated(J["delta"]["decision_lost"], V["delta"]["decision_lost"]),
        passed=bool(dsep is not None and dsep >= 0.15
                    and ci_separated(J["delta"]["decision_lost"], V["delta"]["decision_lost"])))
    preds["P-DP-2"] = dict(
        which_retained_V=V["delta"]["which_retained"]["p"], which_retained_J=J["delta"]["which_retained"]["p"],
        incoh_lost_V=V["delta"]["incoherent_lost"]["p"], incoh_lost_J=J["delta"]["incoherent_lost"]["p"],
        passed=bool(J["delta"]["which_retained"]["p"] is not None
                    and V["delta"]["which_retained"]["p"] is not None
                    and J["delta"]["which_retained"]["p"] >= V["delta"]["which_retained"]["p"] + 0.20
                    and V["delta"]["incoherent_lost"]["p"] is not None
                    and J["delta"]["incoherent_lost"]["p"] is not None
                    and V["delta"]["incoherent_lost"]["p"] >= 2 * J["delta"]["incoherent_lost"]["p"]))
    e3a = dict(err_V=V["arm3a"]["error"]["p"], err_J=J["arm3a"]["error"]["p"])
    preds["P-DP-3a"] = dict(**e3a, gap=round(e3a["err_V"] - e3a["err_J"], 4),
                            passed=bool(e3a["err_V"] - e3a["err_J"] >= 0.15))
    b_v, b_j = V["arm3b"], J["arm3b"]
    gap_abs = (b_v["err_witness_absent"]["p"] - b_j["err_witness_absent"]["p"]
               if b_v["err_witness_absent"]["p"] is not None and b_j["err_witness_absent"]["p"] is not None else None)
    gap_pres = (b_v["err_witness_present"]["p"] - b_j["err_witness_present"]["p"]
                if b_v["err_witness_present"]["p"] is not None and b_j["err_witness_present"]["p"] is not None else None)
    preds["P-DP-3b"] = dict(
        guard_pass=bool(b_v["guard_pass_070_both_sides"] and b_j["guard_pass_070_both_sides"]),
        gap_absent=gap_abs, gap_present=gap_pres,
        passed=bool(b_v["guard_pass_070_both_sides"] and b_j["guard_pass_070_both_sides"]
                    and gap_abs is not None and gap_abs >= 0.15
                    and gap_pres is not None and gap_pres <= 0.05))
    # P-DP-4 descriptive: Δ per (domain, model) vs arm3b witness-absent error per (domain, model)
    pairs = []
    for tag in ("teacher", "V", "J"):
        for d, v in R[tag]["delta"]["per_domain"].items():
            if v["delta"] is not None and d in R[tag]["arm3a"]["per_domain"]:
                e = R[tag]["arm3a"]["per_domain"][d]["p"]
                if e is not None:
                    pairs.append((v["delta"], e))
    def spearman(ps):
        if len(ps) < 3:
            return None
        def rank(xs):
            s = sorted(range(len(xs)), key=lambda i: xs[i])
            r = [0.0] * len(xs)
            for pos, i in enumerate(s):
                r[i] = pos
            return r
        rx, ry = rank([p[0] for p in ps]), rank([p[1] for p in ps])
        n = len(ps)
        mx, my = sum(rx) / n, sum(ry) / n
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
        return round(num / den, 4) if den else None
    preds["P-DP-4-descriptive"] = dict(n_cells=len(pairs), spearman=spearman(pairs))
    # P-DP-5: WHICH-lost DPI per student vs teacher (pooled; per-corpus in the battery blocks)
    tw = T["delta"]["which_lost"]
    half = ((tw["ci"][1] - tw["ci"][0]) / 2 if tw["ci"][0] is not None else None)
    preds["P-DP-5"] = dict(
        teacher_which_lost=tw["p"], V_which_lost=V["delta"]["which_lost"]["p"],
        J_which_lost=J["delta"]["which_lost"]["p"], teacher_ci_halfwidth=(round(half, 4) if half else None),
        passed=bool(half is not None
                    and V["delta"]["which_lost"]["p"] is not None
                    and J["delta"]["which_lost"]["p"] is not None
                    and V["delta"]["which_lost"]["p"] <= tw["p"] + half
                    and J["delta"]["which_lost"]["p"] <= tw["p"] + half))
    campaign = ("CONFIRMED" if preds["P-DP-0"]["passed"] and preds["P-DP-1"]["passed"]
                and preds["P-DP-3a"]["passed"]
                else ("VOID" if not preds["P-DP-0"]["passed"] else "NEGATIVE-BRANCH"))
    out = dict(models=models, predictions=preds, campaign_reading=campaign, batteries=R)
    json.dump(out, open(os.path.join(HERE, "distill_parity_results.json"), "w"), indent=1)
    print(json.dumps(dict(predictions=preds, campaign_reading=campaign), indent=1))


if __name__ == "__main__":
    main()
