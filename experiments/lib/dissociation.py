#!/usr/bin/env python3
"""Shared dissociation runner + scorer for the 2026-07-06 high-power / domain campaigns.

Protocol per item, reader = compressor (one model), contract-blind 15-word compaction:
  compress -> decision, which, which_abstain, repair, nonotes
Probes are the v3/v5 suffixes, with an optional paraphrase set (probe_variant in {0,1,2})
so the campaign can show the dissociation is not an artifact of one probe wording.

Scoring reuses the 2026-07-06 CORRECTED parser (last PARAMETER: anchor, colon required) and
splits NONE into no-failure vs missing-data only via string heuristics here; the semantic
judge split lives in the rescore campaign and can be applied to these raw responses later.

Idempotent cache keyed by (model, item, call, variant); hard call cap; token/cost accounting.
Stdlib only. Import: run_model(alias, items, budget_words, variant, cap) and score(items, ...).
"""
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROK = os.path.join(HERE, "..", "grok-pilots", "2026-07-03")
MULTI = os.path.join(HERE, "..", "multimodel", "2026-07-03")
sys.path.insert(0, os.path.join(GROK, "v3"))
sys.path.insert(0, MULTI)
from runner3 import retained, match_param, ANS_RE  # noqa: E402
from providers import chat, cost_usd               # noqa: E402

# ── probes (variant 0 = the v5 canonical wording; 1,2 = paraphrases) ──────────
COMPRESS_SYS = {
    0: "You are a context compaction engine for an operations assistant. Compress the following "
       "record to at most {wl} words. A future analyst will need to answer questions about it, "
       "but you do not know which questions. Output only the compressed notes.",
    1: "Act as a summarization service. Reduce the document below to {wl} words or fewer. Someone "
       "will later query these notes with questions you cannot see. Return only the summary.",
    2: "Your job is to shrink the following file to at most {wl} words for downstream use. The "
       "questions asked of your summary are unknown to you now. Output the condensed notes only.",
}
DECISION = {
    0: " Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.",
    1: " Per the policy above, is the verdict APPROVED or DENIED? Answer exactly: ANSWER: APPROVED or ANSWER: DENIED.",
    2: " Decide APPROVED or DENIED under the stated policy. Respond exactly: ANSWER: APPROVED or ANSWER: DENIED.",
}
WHICH = {
    0: " If the decision is DENIED, name the single parameter whose reading caused it. Reply exactly: PARAMETER: <name> or PARAMETER: NONE.",
    1: " When the verdict is DENIED, which one parameter's reading is responsible? Answer exactly: PARAMETER: <name>, or PARAMETER: NONE if none.",
    2: " For a DENIED verdict, identify the single failing parameter. Reply exactly with PARAMETER: <name> (or PARAMETER: NONE).",
}
ABSTAIN = {
    0: " If the notes do not contain enough information to determine this, reply exactly: PARAMETER: INSUFFICIENT_EVIDENCE.",
    1: " If the summary lacks the information needed to decide, reply exactly: PARAMETER: INSUFFICIENT_EVIDENCE.",
    2: " Should the notes be insufficient to tell, reply exactly: PARAMETER: INSUFFICIENT_EVIDENCE.",
}
REPAIR = {
    0: " What is the minimal single-parameter change that would flip the decision to APPROVED? Reply exactly: CHANGE: <parameter> to <value>.",
    1: " Give the smallest one-parameter change that would make the verdict APPROVED. Reply exactly: CHANGE: <parameter> to <value>.",
    2: " Identify the single minimal parameter adjustment that flips the outcome to APPROVED. Reply exactly: CHANGE: <parameter> to <value>.",
}
NONOTES = {
    0: " Based only on the policy and general plausibility (no case notes), guess: ANSWER: APPROVED or ANSWER: DENIED.",
    1: " Using only the policy and priors, with no notes provided, guess: ANSWER: APPROVED or ANSWER: DENIED.",
    2: " With no case data, from the policy alone, make your best guess: ANSWER: APPROVED or ANSWER: DENIED.",
}

# ── corrected parser (2026-07-06): last PARAMETER: anchor, colon required ─────
PARAM_COLON_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)
CHANGE_RE = re.compile(r"CHANGE:?\s*\**\s*(.+?)\s+to\s+(-?\d+(?:\.\d+)?)", re.I)
# missing-data heuristic (coarse; the semantic judge is the authority — see rescore campaign)
MISSING_RE = re.compile(r"not (?:present|provided|include|available|contain|specified|given|listed|mention)"
                        r"|missing|absent|no (?:reading|value|measurement|data|information)|"
                        r"cannot (?:determine|verify|confirm)|insufficient|not enough", re.I)


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


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)  # empty cell — keep the results JSON strict-parseable
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(max(0.0, c - h), 4), round(min(1.0, c + h), 4))


def load_cache(raw_path):
    cache = {}
    if os.path.exists(raw_path):
        for line in open(raw_path):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"], r["variant"])] = r
    return cache


def run_model(alias, items, raw_path, budget_words=15, variant=0, cap=100000):
    """Run the full protocol for one model over `items`. Idempotent; appends to raw_path."""
    cache = load_cache(raw_path)
    n0 = len(cache)

    def api(call, messages):
        key = (alias, iid, call, variant)
        if key in cache:
            return cache[key]["text"]
        if len(cache) - n0 + 1 > cap:
            print(f"HARD CAP {cap} reached for {alias}", flush=True)
            sys.exit(2)
        text, usage = chat(alias, messages)
        rec = dict(model=alias, item=iid, call=call, variant=variant, text=text, usage=usage)
        with open(raw_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        cache[key] = rec
        return text

    for n, it in enumerate(items):
        iid = it["id"]
        csys = COMPRESS_SYS[variant].format(wl=budget_words)
        summary = api("compress", [{"role": "system", "content": csys},
                                   {"role": "user", "content": it["document"]}])
        notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
        api("decision", [{"role": "user", "content": notes + DECISION[variant]}])
        api("which", [{"role": "user", "content": notes + WHICH[variant]}])
        api("which_abstain", [{"role": "user", "content": notes + WHICH[variant] + ABSTAIN[variant]}])
        api("repair", [{"role": "user", "content": notes + REPAIR[variant]}])
        api("nonotes", [{"role": "user", "content": it["policy_text"] + "\n\n" + NONOTES[variant]}])
        if (n + 1) % 25 == 0:
            print(f"  {alias} v{variant} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


def score(items, raw_path, variant=0, models=None):
    """Score the dissociation. Returns dict keyed by model with lost/retained cells + CIs."""
    cache = load_cache(raw_path)
    by_item = {it["id"]: it for it in items}
    seen_models = models or sorted({k[0] for k in cache})
    out = {}
    for alias in seen_models:
        rows = []
        for it in items:
            iid = it["id"]
            g = lambda call: cache.get((alias, iid, call, variant), {}).get("text")
            if g("compress") is None:
                continue
            summary = g("compress")
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            dtxt = g("decision") or ""
            m = ANS_RE.search(dtxt)
            decision = m.group(1).upper() if m else None
            wp, wraw = parse_which(g("which"), it["parameters"])
            ab, _ = parse_which(g("which_abstain"), it["parameters"])
            rtxt = g("repair") or ""
            rm = CHANGE_RE.search(rtxt)
            ntxt = g("nonotes") or ""
            nm = ANS_RE.search(ntxt) or re.search(r"\b(APPROVED|DENIED)\b", ntxt, re.I)
            row = dict(
                item=iid, truth=it["truth"], failing=it["failing_param"],
                fail_retained=(retained(summary, fail["value"]) if fail else None),
                any_policy_lost=not all(retained(summary, p["value"]) for p in pol),
                decision=decision, decision_correct=(decision == it["truth"]),
                which=wp, which_raw=wraw,
                which_correct=(wp == (it["failing_param"] or "NONE")),
                which_confab=(wp not in (None, "NONE", "INSUFFICIENT_EVIDENCE", "UNMATCHED")
                              and wp != it["failing_param"]),
                which_none=(wp == "NONE"),
                none_missing=(wp == "NONE" and bool(MISSING_RE.search(g("which") or ""))),
                incoherent=(decision == "DENIED" and wp == "NONE"),
                abstained=(ab == "INSUFFICIENT_EVIDENCE"),
                repair_specific=bool(rm),
                # does a fabricated repair happen to hit the true failing parameter? under
                # witness loss this should sit near the 1/3 candidate-guess floor (J>=S:
                # the policy text discloses the 3 candidates); well above it means a leak.
                repair_param_correct=bool(rm and it["failing_param"] and
                                          match_param(rm.group(1), it["parameters"])
                                          == it["failing_param"]),
                nn_decision=(nm.group(1).upper() if nm else None))
            rows.append(row)
        den = [r for r in rows if r["truth"] == "DENIED"]
        lost = [r for r in den if r["fail_retained"] is False]
        kept = [r for r in den if r["fail_retained"] is True]
        app = [r for r in rows if r["truth"] == "APPROVED"]

        def cell(sub, key):
            k = sum(1 for r in sub if r[key])
            return dict(k=k, n=len(sub), p=(round(k / len(sub), 4) if sub else None),
                        ci=wilson(k, len(sub)))
        # balanced-accuracy prior guard (P-E style): degenerate always-DENY scores 0.5
        nn_deny = sum(1 for r in den if r["nn_decision"] == "DENIED")
        nn_app_deny = sum(1 for r in app if r["nn_decision"] == "DENIED")
        out[alias] = dict(
            n_denied=len(den), n_lost=len(lost), n_kept=len(kept), n_approved=len(app),
            fail_retention=round(sum(r["fail_retained"] for r in den) / len(den), 4) if den else None,
            decision_lost=cell(lost, "decision_correct"),
            which_lost=cell(lost, "which_correct"),
            which_retained=cell(kept, "which_correct"),
            which_confab_lost=cell(lost, "which_confab"),
            incoherent_lost=cell(lost, "incoherent"),
            none_missing_lost=cell([r for r in lost if r["which_none"]], "none_missing"),
            abstain_lost=cell(lost, "abstained"),
            abstain_retained=cell(kept, "abstained"),
            repair_specific_lost=cell(lost, "repair_specific"),
            repair_param_correct_lost=cell(lost, "repair_param_correct"),
            nonotes_deny_rate=round(nn_deny / len(den), 4) if den else None,
            approved_denied_under_loss=round(nn_app_deny / len(app), 4) if app else None,
            rows=rows)
    return out
