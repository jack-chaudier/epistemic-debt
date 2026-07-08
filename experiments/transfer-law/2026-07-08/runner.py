#!/usr/bin/env python3
"""Law-3 cached-summary transfer test. See prereg_transfer_law.md.

  smoke --model grok|haiku|gpt     # 3 counterfactual items, prints raw outputs
  run   --model grok|haiku|gpt     # all 90 items for one model
  run   --model all                # all three working .env-backed models
  score                            # aggregates cached responses, writes results + scored.csv

This campaign reuses the domain-battery compressed summaries. It does NOT make new
compression calls; it asks counterfactual policy probes over cached summaries and full docs.
Stdlib only; idempotent cache in responses_raw.jsonl; token/cost accounting.
"""
import argparse
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "lib"))
import dissociation as X  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import ANS_RE, retained  # noqa: E402
sys.path.insert(0, os.path.join(REPO, "experiments", "multimodel", "2026-07-03"))
from providers import chat, cost_usd  # noqa: E402

ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "transfer_law_results.json")
SOURCE_RAW = os.path.join(REPO, "experiments", "domains", "2026-07-06", "responses_raw.jsonl")
MODELS = ["grok", "haiku", "gpt"]
HARD_CAP = 2000

CF_DECISION = " Under the counterfactual policy above, was the decision APPROVED or DENIED? Reply exactly: ANSWER: APPROVED or ANSWER: DENIED."
CF_WHICH = " If the counterfactual decision is DENIED, name the single parameter whose reading caused it. Reply exactly: PARAMETER: <name> or PARAMETER: NONE."
CF_ABSTAIN = " If the notes do not contain enough information to determine this, reply exactly: PARAMETER: INSUFFICIENT_EVIDENCE."
CF_NONOTES = " Based only on the counterfactual policy and general plausibility (no case notes), guess: ANSWER: APPROVED or ANSWER: DENIED."

PREDICTIONS = {
    "P-L3-1_full_doc_sanity": "full-document counterfactual decision accuracy >= 0.90",
    "P-L3-2_original_accuracy_guard": "cached-summary original decision accuracy >= 0.70 (otherwise not hidden debt)",
    "P-L3-3_witness_conditioned_transfer": "cf decision accuracy with required witness present exceeds missing-witness accuracy by >= 0.20",
    "P-L3-4_reason_channel": "on cf-DENIED items, which_missing < 0.34 and which_retained >= 0.75",
    "P-L3-5_debt_localizes_failure": "among originally-correct rows, missing required cf witness has >=0.20 higher cf error than present witness",
}


def load_items():
    if not os.path.exists(ITEMS):
        sys.exit("items.jsonl missing — run gen_items.py first")
    return [json.loads(line) for line in open(ITEMS)]


def load_cache(path):
    cache = {}
    if os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def load_source_cache():
    if not os.path.exists(SOURCE_RAW):
        sys.exit("source domain responses missing; expected experiments/domains/2026-07-06/responses_raw.jsonl")
    cache = {}
    for line in open(SOURCE_RAW):
        r = json.loads(line)
        if r.get("variant") == 0:
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def prompt_with_notes(item, summary):
    return item["cf_policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"


def prompt_with_doc(item):
    return item["cf_policy_text"] + "\n\nFull case document:\n" + item["document"] + "\n\n"


def call_api(alias, item_id, call, messages, cache, cap):
    key = (alias, item_id, call)
    if key in cache:
        return cache[key]["text"]
    new_calls = sum(1 for k in cache if k[0] == alias and k[2].startswith("cf_"))
    if new_calls + 1 > cap:
        sys.exit(f"HARD CAP {cap} reached for {alias}")
    text, usage = chat(alias, messages)
    rec = {"model": alias, "item": item_id, "call": call, "text": text, "usage": usage}
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key] = rec
    return text


def run_model(alias, items, limit=None, cap=HARD_CAP):
    cache = load_cache(RAW)
    source = load_source_cache()
    if limit:
        items = items[:limit]
    for idx, it in enumerate(items):
        sid = it["source_id"]
        srec = source.get((alias, sid, "compress"))
        odrec = source.get((alias, sid, "decision"))
        if not srec or not odrec:
            sys.exit(f"missing source cached summary/decision for {alias} {sid}")
        notes = prompt_with_notes(it, srec["text"])
        call_api(alias, it["id"], "cf_decision", [{"role": "user", "content": notes + CF_DECISION}], cache, cap)
        call_api(alias, it["id"], "cf_which", [{"role": "user", "content": notes + CF_WHICH}], cache, cap)
        call_api(alias, it["id"], "cf_which_abstain", [{"role": "user", "content": notes + CF_WHICH + CF_ABSTAIN}], cache, cap)
        call_api(alias, it["id"], "cf_nonotes", [{"role": "user", "content": it["cf_policy_text"] + "\n\n" + CF_NONOTES}], cache, cap)
        call_api(alias, it["id"], "cf_full_doc_decision", [{"role": "user", "content": prompt_with_doc(it) + CF_DECISION}], cache, cap)
        if (idx + 1) % 15 == 0:
            print(f"  {alias} {idx + 1}/{len(items)} cached={sum(1 for k in cache if k[0] == alias)}", flush=True)


def parse_decision(text):
    m = ANS_RE.search(text or "") or re.search(r"\b(APPROVED|DENIED)\b", text or "", re.I)
    return m.group(1).upper() if m else None


def cf_required_survived(summary, item):
    if item["cf_truth"] == "DENIED":
        fail = next(p for p in item["cf_parameters"] if p["name"] == item["cf_failing_param"])
        return retained(summary, fail["value"])
    return all(retained(summary, p["value"]) for p in item["cf_parameters"])


def original_required_survived(summary, item):
    pol = [p for p in item["source_parameters"] if p["policy"]]
    if item["source_truth"] == "DENIED":
        fail = next(p for p in pol if p["name"] == item["source_failing_param"])
        return retained(summary, fail["value"])
    return all(retained(summary, p["value"]) for p in pol)


def wilson_cell(rows, pred):
    n = len(rows)
    k = sum(1 for r in rows if pred(r))
    return {"k": k, "n": n, "p": round(k / n, 4) if n else None, "ci": X.wilson(k, n)}


def score_rows(items):
    cache = load_cache(RAW)
    source = load_source_cache()
    rows = []
    for alias in MODELS:
        for it in items:
            sid = it["source_id"]
            srec = source.get((alias, sid, "compress"))
            odrec = source.get((alias, sid, "decision"))
            if not srec or not odrec:
                continue
            if (alias, it["id"], "cf_decision") not in cache:
                continue
            summary = srec["text"]
            cf_decision = parse_decision(cache[(alias, it["id"], "cf_decision")]["text"])
            full_decision = parse_decision(cache[(alias, it["id"], "cf_full_doc_decision")]["text"])
            nn_decision = parse_decision(cache[(alias, it["id"], "cf_nonotes")]["text"])
            orig_decision = parse_decision(odrec["text"])
            which, which_raw = X.parse_which(cache[(alias, it["id"], "cf_which")]["text"], it["cf_parameters"])
            abstain, _ = X.parse_which(cache[(alias, it["id"], "cf_which_abstain")]["text"], it["cf_parameters"])
            rows.append(dict(
                model=alias,
                item=it["id"],
                source_id=sid,
                domain=it["domain"],
                source_truth=it["source_truth"],
                source_failing_param=it["source_failing_param"] or "",
                cf_truth=it["cf_truth"],
                cf_failing_param=it["cf_failing_param"] or "",
                orig_decision=orig_decision or "",
                orig_correct=(orig_decision == it["source_truth"]),
                orig_required_survived=original_required_survived(summary, it),
                cf_required_survived=cf_required_survived(summary, it),
                cf_decision=cf_decision or "",
                cf_decision_correct=(cf_decision == it["cf_truth"]),
                cf_full_doc_decision=full_decision or "",
                cf_full_doc_correct=(full_decision == it["cf_truth"]),
                cf_nonotes_decision=nn_decision or "",
                cf_which=which or "",
                cf_which_raw=which_raw or "",
                cf_which_correct=(which == (it["cf_failing_param"] or "NONE")),
                cf_which_confab=(which not in (None, "NONE", "INSUFFICIENT_EVIDENCE", "UNMATCHED")
                                 and which != it["cf_failing_param"]),
                cf_abstained=(abstain == "INSUFFICIENT_EVIDENCE"),
                summary_words=len(summary.split()),
            ))
    return rows


def summarize(rows):
    out = {"design": {"n_items": len({r["item"] for r in rows}), "models": MODELS,
                       "source": "cached domain-battery summaries", "predictions": PREDICTIONS},
           "per_model": {}, "pooled": {}}
    for alias in MODELS:
        sub = [r for r in rows if r["model"] == alias]
        denied = [r for r in sub if r["cf_truth"] == "DENIED"]
        present = [r for r in sub if r["cf_required_survived"]]
        missing = [r for r in sub if not r["cf_required_survived"]]
        orig_correct = [r for r in sub if r["orig_correct"]]
        orig_present = [r for r in orig_correct if r["cf_required_survived"]]
        orig_missing = [r for r in orig_correct if not r["cf_required_survived"]]
        denied_present = [r for r in denied if r["cf_required_survived"]]
        denied_missing = [r for r in denied if not r["cf_required_survived"]]
        metrics = {
            "n": len(sub),
            "orig_decision_accuracy": wilson_cell(sub, lambda r: r["orig_correct"]),
            "cf_full_doc_accuracy": wilson_cell(sub, lambda r: r["cf_full_doc_correct"]),
            "cf_decision_accuracy": wilson_cell(sub, lambda r: r["cf_decision_correct"]),
            "cf_required_survival": wilson_cell(sub, lambda r: r["cf_required_survived"]),
            "cf_decision_when_required_present": wilson_cell(present, lambda r: r["cf_decision_correct"]),
            "cf_decision_when_required_missing": wilson_cell(missing, lambda r: r["cf_decision_correct"]),
            "cf_error_orig_correct_present": wilson_cell(orig_present, lambda r: not r["cf_decision_correct"]),
            "cf_error_orig_correct_missing": wilson_cell(orig_missing, lambda r: not r["cf_decision_correct"]),
            "cf_which_denied_present": wilson_cell(denied_present, lambda r: r["cf_which_correct"]),
            "cf_which_denied_missing": wilson_cell(denied_missing, lambda r: r["cf_which_correct"]),
            "cf_abstain_denied_present": wilson_cell(denied_present, lambda r: r["cf_abstained"]),
            "cf_abstain_denied_missing": wilson_cell(denied_missing, lambda r: r["cf_abstained"]),
            "mean_summary_words": round(sum(r["summary_words"] for r in sub) / len(sub), 2) if sub else None,
        }
        pres = metrics["cf_decision_when_required_present"]["p"]
        miss = metrics["cf_decision_when_required_missing"]["p"]
        e_pres = metrics["cf_error_orig_correct_present"]["p"]
        e_miss = metrics["cf_error_orig_correct_missing"]["p"]
        w_pres = metrics["cf_which_denied_present"]["p"]
        w_miss = metrics["cf_which_denied_missing"]["p"]
        metrics["transfer_gap_present_minus_missing"] = round(pres - miss, 4) if pres is not None and miss is not None else None
        metrics["debt_error_gap_missing_minus_present"] = round(e_miss - e_pres, 4) if e_pres is not None and e_miss is not None else None
        preds = {
            "P-L3-1_full_doc_sanity": metrics["cf_full_doc_accuracy"]["p"] is not None and metrics["cf_full_doc_accuracy"]["p"] >= 0.90,
            "P-L3-2_original_accuracy_guard": metrics["orig_decision_accuracy"]["p"] is not None and metrics["orig_decision_accuracy"]["p"] >= 0.70,
            "P-L3-3_witness_conditioned_transfer": metrics["transfer_gap_present_minus_missing"] is not None and metrics["transfer_gap_present_minus_missing"] >= 0.20,
            "P-L3-4_reason_channel": w_miss is not None and w_pres is not None and w_miss < 0.34 and w_pres >= 0.75,
            "P-L3-5_debt_localizes_failure": metrics["debt_error_gap_missing_minus_present"] is not None and metrics["debt_error_gap_missing_minus_present"] >= 0.20,
        }
        out["per_model"][alias] = {"metrics": metrics, "predictions": preds}
    pooled = list(rows)
    present = [r for r in pooled if r["cf_required_survived"]]
    missing = [r for r in pooled if not r["cf_required_survived"]]
    out["pooled"] = {
        "n": len(pooled),
        "cf_decision_when_required_present": wilson_cell(present, lambda r: r["cf_decision_correct"]),
        "cf_decision_when_required_missing": wilson_cell(missing, lambda r: r["cf_decision_correct"]),
    }
    a = out["pooled"]["cf_decision_when_required_present"]["p"]
    b = out["pooled"]["cf_decision_when_required_missing"]["p"]
    out["pooled"]["transfer_gap_present_minus_missing"] = round(a - b, 4) if a is not None and b is not None else None
    tok = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            t = tok.setdefault(r["model"], {"prompt": 0, "completion": 0})
            t["prompt"] += r["usage"]["prompt"]
            t["completion"] += r["usage"]["completion"]
    out["cost_usd"] = {a: round(cost_usd(a, tok[a]), 4) for a in tok}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    return out


def do_score():
    items = load_items()
    rows = score_rows(items)
    with open(SCORED, "w", newline="") as f:
        fields = ["model", "item", "source_id", "domain", "source_truth", "source_failing_param",
                  "cf_truth", "cf_failing_param", "orig_decision", "orig_correct",
                  "orig_required_survived", "cf_required_survived", "cf_decision",
                  "cf_decision_correct", "cf_full_doc_decision", "cf_full_doc_correct",
                  "cf_nonotes_decision", "cf_which", "cf_which_raw", "cf_which_correct",
                  "cf_which_confab", "cf_abstained", "summary_words"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    out = summarize(rows)
    json.dump(out, open(RESULTS, "w"), indent=1)
    for alias in MODELS:
        g = out["per_model"].get(alias, {})
        if not g:
            continue
        m = g["metrics"]
        print(f"\n=== {alias} ===")
        print(f"n={m['n']} orig_acc={m['orig_decision_accuracy']['p']} full_doc_cf={m['cf_full_doc_accuracy']['p']} cf_acc={m['cf_decision_accuracy']['p']}")
        print(f"cf_required_survival={m['cf_required_survival']['p']} present_cf={m['cf_decision_when_required_present']['p']} missing_cf={m['cf_decision_when_required_missing']['p']} gap={m['transfer_gap_present_minus_missing']}")
        print(f"cf_which present/missing={m['cf_which_denied_present']['p']}/{m['cf_which_denied_missing']['p']} abstain present/missing={m['cf_abstain_denied_present']['p']}/{m['cf_abstain_denied_missing']['p']}")
        print(f"debt_error_gap={m['debt_error_gap_missing_minus_present']} predictions={g['predictions']}")
    print(f"\nwrote {SCORED}")
    print(f"wrote {RESULTS}")
    print(f"total cost: ${out['total_cost_usd']}")


def do_smoke(alias):
    items = load_items()[:3]
    run_model(alias, items, limit=3, cap=HARD_CAP)
    cache = load_cache(RAW)
    for it in items:
        print(f"\n--- {it['id']} source={it['source_truth']} cf={it['cf_truth']} cf_fail={it['cf_failing_param']}")
        for call in ("cf_decision", "cf_which", "cf_which_abstain", "cf_nonotes", "cf_full_doc_decision"):
            txt = cache.get((alias, it["id"], call), {}).get("text")
            print(f"  [{call}] {txt}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["smoke", "run", "score"])
    ap.add_argument("--model", choices=MODELS + ["all"])
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.cmd == "score":
        do_score()
        return
    if not args.model:
        sys.exit("--model required for smoke/run")
    if args.cmd == "smoke":
        if args.model == "all":
            for alias in MODELS:
                do_smoke(alias)
        else:
            do_smoke(args.model)
        return
    items = load_items()
    models = MODELS if args.model == "all" else [args.model]
    for alias in models:
        run_model(alias, items, limit=args.limit, cap=HARD_CAP)
        print(f"{alias} done")


if __name__ == "__main__":
    main()
