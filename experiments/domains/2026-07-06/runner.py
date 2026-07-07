#!/usr/bin/env python3
"""Tier-2 domain-battery dissociation run + scorer. See prereg_domains.md.

  run   --model grok|haiku|gpt [--domain <key>] [--limit N]
  smoke --model grok                 # 3 items (one domain) end-to-end, prints raw
  score                              # per-domain x per-model cells + predictions

Reader = compressor, 15-word contract-blind compaction, 6 domains x 100 items. Idempotent
cache in responses_raw.jsonl; hard cap 20000/model. Stdlib only.
"""
import argparse
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import dissociation as X
import domains as D
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from providers import cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "domains_results.json")
BUDGET_WORDS = 15
HARD_CAP = 20000
MODELS = ["grok", "haiku", "gpt"]
VARIANT = 0
PREDICTIONS = {
    "P-D1_dissociation_per_domain": "which_lost.ci upper < which_retained.ci lower AND which_lost.p < 0.34, per (model,domain) with a populated split",
    "P-D2_verdict_survives": "decision_lost.p >= 0.70 per (model,domain)",
    "P-D3_generalizes": "P-D1 holds on >= 5 of 6 domains for each model that is applicable (retention in (0.15,0.85) so the split is populated)",
}


def load_items():
    path = os.path.join(HERE, "items.jsonl")
    if not os.path.exists(path):
        sys.exit("items.jsonl missing — run gen_items.py first")
    return [json.loads(l) for l in open(path)]


def do_score():
    items = load_items()
    by_domain = defaultdict(list)
    for it in items:
        by_domain[it["domain"]].append(it)
    cache_models = sorted({json.loads(l)["model"] for l in open(RAW)}) if os.path.exists(RAW) else []
    out = {"design": dict(domains=list(by_domain), n_per_domain=len(next(iter(by_domain.values()))),
                          budget_words=BUDGET_WORDS, reader="compressor", predictions=PREDICTIONS),
           "cells": {}}
    tok = {}
    if os.path.exists(RAW):
        for l in open(RAW):
            r = json.loads(l)
            t = tok.setdefault(r["model"], dict(prompt=0, completion=0))
            t["prompt"] += r["usage"]["prompt"]
            t["completion"] += r["usage"]["completion"]
    # per (model, domain)
    summary_pass = defaultdict(lambda: dict(applicable=0, passed=0))
    for domain, ditems in by_domain.items():
        res = X.score(ditems, RAW, variant=VARIANT, models=cache_models)
        for alias, r in res.items():
            r.pop("rows", None)
            applicable = (r["fail_retention"] is not None and 0.15 < r["fail_retention"] < 0.85
                          and r["n_lost"] >= 5 and r["n_kept"] >= 5)
            d1 = None
            if applicable:
                d1 = bool(r["which_lost"]["ci"][1] < r["which_retained"]["ci"][0] and
                          r["which_lost"]["p"] is not None and r["which_lost"]["p"] < 0.34)
                summary_pass[alias]["applicable"] += 1
                summary_pass[alias]["passed"] += int(d1)
            d2 = bool(r["decision_lost"]["p"] is not None and r["decision_lost"]["p"] >= 0.70)
            out["cells"][f"{alias}/{domain}"] = dict(
                metrics=r, applicable=applicable, P_D1=d1, P_D2=d2)
    out["P_D3_generalizes"] = {a: dict(applicable=v["applicable"], passed=v["passed"],
                                       holds=bool(v["applicable"] >= 1 and v["passed"] >= min(5, v["applicable"])))
                               for a, v in summary_pass.items()}
    out["cost_usd"] = {a: round(cost_usd(a, tok[a]), 4) for a in tok}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    # console
    for alias in cache_models:
        print(f"\n=== {alias} ===")
        for domain in by_domain:
            c = out["cells"].get(f"{alias}/{domain}")
            if not c:
                continue
            m = c["metrics"]
            tag = "" if c["applicable"] else "  (inapplicable: retention/​split)"
            print(f"  {domain:16} ret={m['fail_retention']} lost={m['n_lost']} kept={m['n_kept']} "
                  f"which_lost={m['which_lost']['p']}{m['which_lost']['ci']} "
                  f"which_ret={m['which_retained']['p']} dec_lost={m['decision_lost']['p']} "
                  f"P-D1={c['P_D1']}{tag}")
        print(f"  P-D3: {out['P_D3_generalizes'].get(alias)}")
    print(f"\ntotal cost: ${out['total_cost_usd']}")
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--domain", choices=D.DOMAIN_KEYS)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    items = load_items()
    if a.domain:
        items = [it for it in items if it["domain"] == a.domain]
    if a.cmd == "smoke":
        items = items[:3]
        X.run_model(a.model, items, RAW, BUDGET_WORDS, VARIANT, cap=HARD_CAP)
        for it in items:
            print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']}")
            for call in ("compress", "decision", "which", "which_abstain", "repair"):
                txt = next((json.loads(l)["text"] for l in open(RAW)
                            if json.loads(l)["item"] == it["id"] and json.loads(l)["call"] == call
                            and json.loads(l)["variant"] == VARIANT), None)
                print(f"  [{call}] {txt}")
        return
    if a.limit:
        items = items[:a.limit]
    X.run_model(a.model, items, RAW, BUDGET_WORDS, VARIANT, cap=HARD_CAP)
    print(f"{a.model} done ({len(items)} items)")


if __name__ == "__main__":
    main()
