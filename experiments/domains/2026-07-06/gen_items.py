#!/usr/bin/env python3
"""Tier-2 domain battery: 6 structurally distinct domains, one item schema.

Purpose: kill the schema-specificity fear. All prior shelf results used the incident (and one
clinical) corpus. If the dissociation replicates across operations, clinical, software CI,
loan underwriting, vendor SLA, and security triage — six unrelated document registers sharing
only the verdict interface (conjunction-of-3-thresholds, DENIED = one failing) — the shelf is
not a property of the incident schema.

n per domain = 100 (50 APPROVED / 50 DENIED). Fresh per-domain seeds. Writes items.jsonl
(all domains concatenated). No LLM. Deterministic.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D

N_PER_DOMAIN = 100
BASE_SEED = 706020     # per-domain seed = BASE_SEED + index; disjoint from Tier-1 (706010)
ITEMS = os.path.join(HERE, "items.jsonl")


def main():
    all_items, all_problems = [], []
    for idx, key in enumerate(D.DOMAIN_KEYS):
        items = D.gen_items(key, seed=BASE_SEED + idx, n=N_PER_DOMAIN)
        probs = D.selfcheck(items)
        all_problems += [(key, *p) for p in probs]
        all_items += items
        wc = [it["word_count"] for it in items]
        den = sum(it["truth"] == "DENIED" for it in items)
        print(f"{key:18} n={len(items)} DENIED={den} words {min(wc)}-{max(wc)} "
              f"mean{sum(wc)//len(wc)} problems={len(probs)}")
    if all_problems:
        print(f"\nSELFCHECK FAILED ({len(all_problems)}):")
        for p in all_problems[:20]:
            print("  ", p)
        sys.exit(1)
    with open(ITEMS, "w") as f:
        for it in all_items:
            f.write(json.dumps(it) + "\n")
    print(f"\nwrote {len(all_items)} items across {len(D.DOMAIN_KEYS)} domains — selfcheck clean")


if __name__ == "__main__":
    main()
