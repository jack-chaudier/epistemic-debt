#!/usr/bin/env python3
"""EXPLORATORY reanalysis (no API): the 'section' fingerprint — what verdict does each model
emit when the deciding evidence is destroyed, on BOTH verdict sides, versus its no-notes prior.

Motivation (fresh-eyes audit 2026-07-09): evidence absence never produces noise in this
program's data — it produces *systematic* verdicts. Formally: compaction is a quotient map;
the reader on a collapsed fiber emits a learned default representative (a section), not
"unknown". Two disambiguations this script adds to that observation:
  (1) APPROVED-side ablation (kill test for generic-conservatism vs fiber-filling), and
  (2) section vs no-notes prior (kill test for "this is just the bias shelf", rows 8/25).

Data: cached domain-battery responses (2026-07-06, 3 frontier models, 6 domains) and the
distill-parity delta battery (2026-07-08, teacher + both students). Deterministic; exit 0.
Numbers are a scent, not a row: DENIED/APPROVED-lost cells are conditioned on each model's own
compression (self-compressed artifacts), and no perturbation-stability arm has run yet.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained, ANS_RE  # noqa: E402


def dec_last(t):
    m = ANS_RE.findall(t or "")
    if m:
        return m[-1].upper() if isinstance(m[-1], str) else m[-1]
    m = re.findall(r"\b(APPROVED|DENIED)\b", t or "", re.I)
    return m[-1].upper() if m else None


def analyze(items_path, raw_path, models=None):
    items = {it["id"]: it for it in map(json.loads, open(items_path))}
    raw = {}
    for l in open(raw_path):
        r = json.loads(l)
        raw[(r["model"], r["item"], r["call"])] = r["text"]
    out = {}
    for m in (models or sorted({k[0] for k in raw})):
        c = dict(dl_app=0, dl_n=0, kept_app=0, kept_n=0, al_deny=0, al_n=0,
                 ak_deny=0, ak_n=0, nn_app=0, nn_n=0)
        for it in items.values():
            s = raw.get((m, it["id"], "compress"))
            if s is None:
                continue
            d = dec_last(raw.get((m, it["id"], "decision")))
            # PRIOR parse must be strict-anchored: hedged nonotes prose restates the policy,
            # so bare APPROVED/DENIED tokens are echoes, not answers (verified on raw gpt).
            nntxt = raw.get((m, it["id"], "nonotes"))
            if nntxt is not None:
                c["nn_total"] = c.get("nn_total", 0) + 1
                mm = ANS_RE.findall(nntxt)
                if mm:
                    c["nn_n"] += 1
                    c["nn_app"] += (mm[-1].upper() == "APPROVED")
            pol = [p for p in it["parameters"] if p["policy"]]
            if it["truth"] == "DENIED":
                fail = next(p for p in pol if not p["passes"])
                key = ("kept" if retained(s, fail["value"]) else "dl")
                c[key + "_n"] += 1
                c[key + "_app"] += (d == "APPROVED")
            else:
                key = ("ak" if all(retained(s, p["value"]) for p in pol) else "al")
                c[key + "_n"] += 1
                c[key + "_deny"] += (d == "DENIED")
        r_ = lambda k, n: round(c[k] / c[n], 4) if c[n] else None
        out[m] = dict(
            denied_lost_approve=r_("dl_app", "dl_n"), n_denied_lost=c["dl_n"],
            denied_kept_approve=r_("kept_app", "kept_n"),
            approved_lost_deny=r_("al_deny", "al_n"), n_approved_lost=c["al_n"],
            approved_kept_deny=r_("ak_deny", "ak_n"),
            nonotes_approve_anchored=r_("nn_app", "nn_n"), nonotes_anchored_n=c["nn_n"],
            nonotes_unanchored_share=(round(1 - c["nn_n"] / c["nn_total"], 4)
                                      if c.get("nn_total") else None))
    return out


def main():
    res = dict(
        label="EXPLORATORY — reanalysis of cached self-compressed responses; not preregistered",
        domains_2026_07_06=analyze(
            os.path.join(REPO, "experiments", "domains", "2026-07-06", "items.jsonl"),
            os.path.join(REPO, "experiments", "domains", "2026-07-06", "responses_raw.jsonl")),
        distill_parity_delta=analyze(
            os.path.join(REPO, "experiments", "distill-parity", "2026-07-08", "delta_battery.jsonl"),
            os.path.join(REPO, "experiments", "distill-parity", "2026-07-08", "responses_raw.jsonl"),
            models=["Qwen/Qwen3-8B", "sv1", "sj1"]))
    json.dump(res, open(os.path.join(HERE, "sections_reanalysis.json"), "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
