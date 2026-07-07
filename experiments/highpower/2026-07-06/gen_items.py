#!/usr/bin/env python3
"""Tier-1 high-power corpus: one domain (ops_incident), fresh seed, large n.

Purpose: shrink the statistical-n fear. Prior cells were 14-22 items; at n=200 DENIED,
lost/retained cells land near 120/80, tightening Wilson CIs from ~+/-0.15 to ~+/-0.05.
Writes items.jsonl next to this file. No LLM. Deterministic in SEED.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D

SEED = 706010          # fresh; disjoint from every prior corpus seed
N = 400                # 200 APPROVED / 200 DENIED
DOMAIN = "ops_incident"
ITEMS = os.path.join(HERE, "items.jsonl")


def main():
    items = D.gen_items(DOMAIN, seed=SEED, n=N)
    problems = D.selfcheck(items)
    if problems:
        print(f"SELFCHECK FAILED ({len(problems)}):")
        for p in problems[:20]:
            print("  ", p)
        sys.exit(1)
    with open(ITEMS, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    den = [it for it in items if it["truth"] == "DENIED"]
    wc = [it["word_count"] for it in items]
    print(f"wrote {len(items)} items ({len(den)} DENIED) to items.jsonl")
    print(f"words min={min(wc)} max={max(wc)} mean={sum(wc)/len(wc):.0f}")
    print(f"fail slots: {[sum(it['fail_slot'] == k for it in items) for k in (0, 1, 2)]}")
    print("selfcheck: clean")


if __name__ == "__main__":
    main()
