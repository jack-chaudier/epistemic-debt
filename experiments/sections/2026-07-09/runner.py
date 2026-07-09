#!/usr/bin/env python3
"""Sections campaign runner: smoke / run / score. Stdlib only; providers via multimodel.

    python3 runner.py smoke                  # 3 items end-to-end on every probe, all models
    python3 runner.py run --model all        # full battery (idempotent cache, hard cap)
    python3 runner.py score                  # fingerprint table + P-SEC-* -> sections_results.json

Contract: temperature 0 (providers default), cache keyed (model,item,call), strict
last-ANSWER-anchor parsing, unanchored counted as hedges (never binned). Prereg:
prereg_sections.md (frozen before spend).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "multimodel", "2026-07-03"))
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from providers import chat, cost_usd  # noqa: E402
from runner3 import retained  # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
MODELS = ["grok", "haiku", "gpt"]
CAP = 8000
MEASURE_DOMAINS = {"ops_incident", "clinical_enroll", "ci_release"}
PERTURB_DOMAINS = {"ops_incident", "clinical_enroll"}

DECISION = (" Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED "
            "or ANSWER: DENIED.")
DECISION_V1 = (" Per the policy above, is the verdict APPROVED or DENIED? Answer exactly: "
               "ANSWER: APPROVED or ANSWER: DENIED.")
ABSTAIN = (" If the file does not contain enough information to determine this, reply exactly: "
           "ANSWER: INSUFFICIENT_EVIDENCE.")
NONOTES = (" Based only on the policy and general plausibility (no case notes), guess: "
           "ANSWER: APPROVED or ANSWER: DENIED.")
ANS_RE = re.compile(r"ANSWER\s*:\s*\**\s*(APPROVED|DENIED|INSUFFICIENT_EVIDENCE)", re.I)


def doc_prompt(it, doc, req):
    return it["policy_text"] + "\n\nCase file:\n" + doc + "\n\n" + req.strip()


def calls_for(it):
    c = [("nonotes", it["policy_text"] + "\n\n" + NONOTES.strip()),
         ("ctrl_decision", doc_prompt(it, it["document"], DECISION)),
         ("abl_decision", doc_prompt(it, it["document_ablated"], DECISION)),
         ("abl_abstain", doc_prompt(it, it["document_ablated"], DECISION + ABSTAIN))]
    if it["domain"] in PERTURB_DOMAINS:
        c.append(("abl_shuffle", doc_prompt(it, it["document_ablated_shuffled"], DECISION)))
        c.append(("abl_reword", doc_prompt(it, it["document_ablated"], DECISION_V1)))
    return c


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def run(models, items, limit=0):
    cache = load_cache()
    n0 = len(cache)
    spend = {m: 0.0 for m in models}
    for m in models:
        done = 0
        for it in (items[:limit] if limit else items):
            for call, prompt in calls_for(it):
                key = (m, it["id"], call)
                if key in cache:
                    continue
                if len(cache) - n0 + 1 > CAP:
                    print(f"HARD CAP {CAP}")
                    sys.exit(2)
                text, usage = chat(m, [dict(role="user", content=prompt)])
                rec = dict(model=m, item=it["id"], call=call, text=text, usage=usage)
                with open(RAW, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                cache[key] = rec
                spend[m] += cost_usd(m, usage)
            done += 1
            if done % 40 == 0:
                print(f"  {m} {done}/{limit or len(items)} (${spend[m]:.2f})", flush=True)
        print(f"{m} done, new spend ${spend[m]:.4f}", flush=True)
    print(f"total new spend ${sum(spend.values()):.4f}; {len(cache)} records")


def ans(text):
    m = ANS_RE.findall(text or "")
    return m[-1].upper() if m else None


def score():
    items = [json.loads(l) for l in open(os.path.join(HERE, "items.jsonl"))]
    by_id = {it["id"]: it for it in items}
    cache = load_cache()
    g = lambda m, i, c: (cache.get((m, i, c)) or {}).get("text")
    out = dict(models={}, predictions={})
    for m in MODELS:
        M = {}
        # section: ablated cells, pooled + per side + per domain
        def cell(pred):
            txts = [g(m, it["id"], "abl_decision") for it in items if pred(it)]
            a = [ans(t) for t in txts if t is not None]
            anch = [x for x in a if x in ("APPROVED", "DENIED")]
            n = len(anch)
            return dict(n_total=len(a), n_anchored=n,
                        approve=(round(sum(x == "APPROVED" for x in anch) / n, 4) if n else None),
                        hedge_share=(round(1 - n / len(a), 4) if a else None))
        pooled = cell(lambda it: True)
        appr = pooled["approve"]
        section = "APPROVED" if appr is not None and appr >= 0.5 else "DENIED"
        strength = max(appr, 1 - appr) if appr is not None else None
        per_domain = {d: cell(lambda it, d=d: it["domain"] == d)
                      for d in sorted({it["domain"] for it in items})}
        strengths = [max(v["approve"], 1 - v["approve"]) for v in per_domain.values()
                     if v["approve"] is not None]
        # prior + control + abstain + perturbations
        def channel(callname, pred=lambda it: True):
            txts = [g(m, it["id"], callname) for it in items if pred(it)]
            a = [ans(t) for t in txts if t is not None]
            anch = [x for x in a if x in ("APPROVED", "DENIED")]
            n = len(anch)
            return dict(n_total=len(a), n_anchored=n,
                        approve=(round(sum(x == "APPROVED" for x in anch) / n, 4) if n else None),
                        abstain=(round(sum(x == "INSUFFICIENT_EVIDENCE" for x in a) / len(a), 4)
                                 if a else None),
                        unanchored=(round(sum(x is None for x in a) / len(a), 4) if a else None))
        prior = channel("nonotes")
        ctrl_err = None
        ctrl = [(ans(g(m, it["id"], "ctrl_decision")), it["truth"]) for it in items]
        canch = [(x, t) for x, t in ctrl if x in ("APPROVED", "DENIED")]
        if canch:
            ctrl_err = round(sum(x != t for x, t in canch) / len(canch), 4)
        pert = {p: channel(p, lambda it: it["domain"] in PERTURB_DOMAINS)
                for p in ("abl_shuffle", "abl_reword")}
        base_pert = channel("abl_decision", lambda it: it["domain"] in PERTURB_DOMAINS)
        # forecast: section from measurement domains -> sign-hit on held-out
        meas = cell(lambda it: it["domain"] in MEASURE_DOMAINS)
        sec_meas = "APPROVED" if (meas["approve"] or 0) >= 0.5 else "DENIED"
        wrong = []
        for it in items:
            if it["domain"] in MEASURE_DOMAINS:
                continue
            x = ans(g(m, it["id"], "abl_decision"))
            if x in ("APPROVED", "DENIED") and x != it["truth"]:
                wrong.append(x)
        hit = (round(sum(w == sec_meas for w in wrong) / len(wrong), 4) if wrong else None)
        hit_sv1 = (round(sum(w == "APPROVED" for w in wrong) / len(wrong), 4) if wrong else None)
        truth_marginal = (round(max(sum(w == "APPROVED" for w in wrong),
                                    sum(w == "DENIED" for w in wrong)) / len(wrong), 4)
                          if wrong else None)
        M.update(section=section, strength=(round(strength, 4) if strength else None),
                 pooled=pooled, per_domain=per_domain,
                 domain_strength_range=(round(max(strengths) - min(strengths), 4)
                                        if strengths else None),
                 prior=prior, ctrl_error=ctrl_err,
                 abstain_channel=channel("abl_abstain"),
                 perturb=dict(base=base_pert, **pert),
                 forecast=dict(section_meas=sec_meas, n_wrong_heldout=len(wrong),
                               sign_hit=hit, null_coin=0.5, null_truth_marginal=truth_marginal,
                               hit_via_sv1_section=hit_sv1))
        out["models"][m] = M
    # cached-target transfer + sensitivity annex are separate scripts (score_cached.py)
    P = out["predictions"]
    for m, M in out["models"].items():
        sh = [abs((M["perturb"][p]["approve"] or 0) - (M["perturb"]["base"]["approve"] or 0))
              for p in ("abl_shuffle", "abl_reword")]
        P.setdefault("P-SEC-1", {})[m] = dict(
            strength=M["strength"], range=M["domain_strength_range"], shifts=[round(x, 4) for x in sh],
            passed=bool(M["strength"] is not None and M["strength"] >= 0.75
                        and M["domain_strength_range"] is not None
                        and M["domain_strength_range"] <= 0.25 and all(x <= 0.10 for x in sh)))
        gap = (abs((M["pooled"]["approve"] or 0) - (M["prior"]["approve"] or 0))
               if M["pooled"]["approve"] is not None and M["prior"]["approve"] is not None else None)
        P.setdefault("P-SEC-2", {})[m] = dict(gap=(round(gap, 4) if gap is not None else None),
                                              passed=bool(gap is not None and gap >= 0.25))
        f = M["forecast"]
        P.setdefault("P-SEC-3a", {})[m] = dict(
            sign_hit=f["sign_hit"], nulls=dict(coin=0.5, truth_marginal=f["null_truth_marginal"]),
            cross_model_margin=(round((f["sign_hit"] or 0) - (f["hit_via_sv1_section"] or 0), 4)
                                if f["sign_hit"] is not None else None),
            passed=bool(f["sign_hit"] is not None and f["sign_hit"] >= 0.80
                        and (f["sign_hit"] - (f["hit_via_sv1_section"] or 0)) >= 0.30))
    n1 = sum(P["P-SEC-1"][m]["passed"] for m in MODELS)
    n2 = sum(P["P-SEC-2"][m]["passed"] for m in MODELS)
    n3 = sum(P["P-SEC-3a"][m]["passed"] for m in MODELS)
    out["campaign_reading"] = dict(
        p_sec_1=f"{n1}/3", p_sec_2=f"{n2}/3", p_sec_3a=f"{n3}/3",
        upheld=bool(n1 >= 2 and n2 >= 2 and n3 >= 2))
    json.dump(out, open(os.path.join(HERE, "sections_results.json"), "w"), indent=1)
    print(json.dumps(dict(predictions=out["predictions"],
                          campaign_reading=out["campaign_reading"]), indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["smoke", "run", "score"])
    ap.add_argument("--model", default="all")
    a = ap.parse_args()
    if a.mode == "score":
        score()
        return
    items = [json.loads(l) for l in open(os.path.join(HERE, "items.jsonl"))]
    models = MODELS if a.model == "all" else [a.model]
    run(models, items, limit=(3 if a.mode == "smoke" else 0))


if __name__ == "__main__":
    main()
