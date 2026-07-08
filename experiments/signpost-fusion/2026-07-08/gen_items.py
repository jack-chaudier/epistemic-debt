#!/usr/bin/env python3
"""B5a fusion-contract pilot — corpus generator (see prereg_fusion.md).

3 confound-guarded domains x 30 items = 90 items, using the shared generators in
experiments/lib/domains.py (identical verdict interface across domains). Deterministic in the
seeds below; mechanical selfcheck (salience / verdict-leak / value-collision) must pass with
zero problems before any API spend.

  python3 gen_items.py            # writes items.jsonl, runs selfcheck
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D  # noqa: E402

DOMAINS = ["ops_incident", "clinical_enroll", "ci_release"]
N_PER = 30
BASE_SEED = 20260708
OUT = os.path.join(HERE, "items.jsonl")


def build():
    items = []
    for di, dom in enumerate(DOMAINS):
        items.extend(D.gen_items(dom, BASE_SEED + di, N_PER))
    problems = D.selfcheck(items)
    if problems:
        for p in problems:
            print("CONFOUND:", p)
        sys.exit(f"selfcheck failed: {len(problems)} problems — not writing")
    with open(OUT, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    n_denied = sum(1 for it in items if it["truth"] == "DENIED")
    wc = [it["word_count"] for it in items]
    print(f"wrote {len(items)} items to {OUT}")
    print(f"  domains={DOMAINS}  denied={n_denied}  approved={len(items) - n_denied}")
    print(f"  doc words: min={min(wc)} mean={sum(wc) // len(wc)} max={max(wc)}")
    print(f"  selfcheck: 0 problems")


if __name__ == "__main__":
    build()
