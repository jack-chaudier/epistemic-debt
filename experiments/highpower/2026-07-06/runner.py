#!/usr/bin/env python3
"""Tier-1 high-power dissociation run + scorer. See prereg_highpower.md.

  run   --model grok|haiku|gpt [--variant 0|1|2] [--limit N]
  smoke --model grok                 # 3 items end-to-end, prints raw outputs
  score                              # aggregates all cached models/variants, writes results

Reader = compressor, 15-word contract-blind compaction, N=400 (200 DENIED). Idempotent
cache in responses_raw.jsonl; hard cap 8000/model. Stdlib only.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import dissociation as X
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from providers import cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "highpower_results.json")
BUDGET_WORDS = 15
HARD_CAP = 8000
MODELS = ["grok", "haiku", "gpt"]
# Preregistered predictions (fixed before spend). CIs are Wilson 95%.
PREDICTIONS = {
    "P-H1_dissociation": "which_lost.ci upper < which_retained.ci lower (non-overlapping); which_lost.p < 0.34 (below 1/3 guess)",
    "P-H2_verdict_survives": "decision_lost.p >= 0.75",
    "P-H3_abstain_detects": "abstain_lost.p >= 0.6 AND abstain_retained.p <= 0.15",
    "P-H4_confab_locus": "repair_specific_lost.p >= 0.6 (action channel fabricates) while which_confab_lost.p <= 0.25",
    "P-H5_prior_guard": "approved_denied_under_loss reported; decision_lost balanced-accuracy vs prior noted (not a pass/fail, characterization)",
}


def load_items():
    path = os.path.join(HERE, "items.jsonl")
    if not os.path.exists(path):
        sys.exit("items.jsonl missing — run gen_items.py first")
    return [json.loads(l) for l in open(path)]


def evaluate(cell_lost, cell_ret):
    lo_ret = cell_ret["ci"][0]
    hi_lost = cell_lost["ci"][1]
    if lo_ret is None or hi_lost is None:
        return False  # empty cell — cannot pass
    return bool(hi_lost < lo_ret)


def do_score():
    items = load_items()
    cache_models = sorted({json.loads(l)["model"] for l in open(RAW)}) if os.path.exists(RAW) else []
    variants = sorted({json.loads(l)["variant"] for l in open(RAW)}) if os.path.exists(RAW) else [0]
    out = {"design": dict(domain="ops_incident", n_items=len(items), budget_words=BUDGET_WORDS,
                          reader="compressor", predictions=PREDICTIONS),
           "by_variant": {}}
    tok = {}
    if os.path.exists(RAW):
        for l in open(RAW):
            r = json.loads(l)
            t = tok.setdefault(r["model"], dict(prompt=0, completion=0))
            t["prompt"] += r["usage"]["prompt"]
            t["completion"] += r["usage"]["completion"]
    for variant in variants:
        res = X.score(items, RAW, variant=variant, models=cache_models)
        graded = {}
        for alias, r in res.items():
            r.pop("rows", None)
            preds = {}
            preds["P-H1_dissociation"] = bool(
                evaluate(r["which_lost"], r["which_retained"]) and
                (r["which_lost"]["p"] is not None and r["which_lost"]["p"] < 0.34))
            preds["P-H2_verdict_survives"] = bool(r["decision_lost"]["p"] is not None and
                                                  r["decision_lost"]["p"] >= 0.75)
            preds["P-H3_abstain_detects"] = bool(
                r["abstain_lost"]["p"] is not None and r["abstain_lost"]["p"] >= 0.6 and
                r["abstain_retained"]["p"] is not None and r["abstain_retained"]["p"] <= 0.15)
            preds["P-H4_confab_locus"] = bool(
                r["repair_specific_lost"]["p"] is not None and r["repair_specific_lost"]["p"] >= 0.6 and
                r["which_confab_lost"]["p"] is not None and r["which_confab_lost"]["p"] <= 0.25)
            graded[alias] = dict(metrics=r, predictions=preds)
        out["by_variant"][str(variant)] = graded
    out["cost_usd"] = {a: round(cost_usd(a, tok[a]), 4) for a in tok}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    # console summary
    for variant, graded in out["by_variant"].items():
        print(f"\n=== variant {variant} ===")
        for alias, g in graded.items():
            m = g["metrics"]
            print(f"{alias}: DENIED={m['n_denied']} lost={m['n_lost']} kept={m['n_kept']} "
                  f"retention={m['fail_retention']}")
            print(f"  which_lost={m['which_lost']['p']} {m['which_lost']['ci']}  "
                  f"which_retained={m['which_retained']['p']} {m['which_retained']['ci']}  "
                  f"decision_lost={m['decision_lost']['p']}")
            print(f"  abstain lost/ret={m['abstain_lost']['p']}/{m['abstain_retained']['p']}  "
                  f"repair_specific_lost={m['repair_specific_lost']['p']}  "
                  f"confab_lost={m['which_confab_lost']['p']}  incoh_lost={m['incoherent_lost']['p']}")
            print(f"  prior: nonotes_deny={m['nonotes_deny_rate']} approved_denied_under_loss={m['approved_denied_under_loss']}")
            print(f"  predictions: {g['predictions']}")
    print(f"\ntotal cost: ${out['total_cost_usd']}")
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--variant", type=int, default=0, choices=[0, 1, 2])
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    items = load_items()
    if a.cmd == "smoke":
        items = items[:3]
        X.run_model(a.model, items, RAW, BUDGET_WORDS, a.variant, cap=HARD_CAP)
        for it in items:
            print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']}")
            for call in ("compress", "decision", "which", "which_abstain", "repair"):
                import json as _j
                txt = next((_j.loads(l)["text"] for l in open(RAW)
                            if _j.loads(l)["item"] == it["id"] and _j.loads(l)["call"] == call
                            and _j.loads(l)["variant"] == a.variant), None)
                print(f"  [{call}] {txt}")
        return
    if a.limit:
        items = items[:a.limit]
    X.run_model(a.model, items, RAW, BUDGET_WORDS, a.variant, cap=HARD_CAP)
    print(f"{a.model} v{a.variant} done ({len(items)} items)")


if __name__ == "__main__":
    main()
