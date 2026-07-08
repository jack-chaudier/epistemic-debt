#!/usr/bin/env python3
"""Regenerated train pool (revision_protocol.md rule 4): 5 G2-kept domains x 1,900 = 9,500.

Same generator, same per-domain seed bases as train_pool.jsonl (812100 + ORIGINAL domain index
in D.DOMAIN_KEYS), so items 0..999 per domain reproduce the original pool byte-for-byte and
items 1000..1899 extend it deterministically (gen_domain's chunked seed-retry rule). Selfcheck
must be clean; overlap with the original pool is asserted on a sample. Writes
train_pool_r1.jsonl."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D  # noqa: E402
from gen_items import gen_domain  # noqa: E402

KEPT = ["clinical_enroll", "ci_release", "loan_underwrite", "vendor_sla", "sec_triage"]
N = 1900

orig = {}
for l in open(os.path.join(HERE, "train_pool.jsonl")):
    it = json.loads(l)
    orig[it["id"]] = it

out = []
for key in KEPT:
    idx = D.DOMAIN_KEYS.index(key)
    batch = gen_domain(key, 812100 + idx, N)
    for j, it in enumerate(batch):
        it["id"] = f"trainpool-{key}-{j:04d}"
        it["split"] = "trainpool"
    out.extend(batch)

problems = D.selfcheck(out)
if problems:
    print(f"SELFCHECK FAILED ({len(problems)}):")
    for p in problems[:20]:
        print("  ", p)
    sys.exit(1)

# overlap assertion: regenerated items 0..999 must equal the committed originals
mismatch = sum(1 for it in out if it["id"] in orig and orig[it["id"]]["document"] != it["document"])
assert mismatch == 0, f"{mismatch} regenerated items diverge from the committed pool"

with open(os.path.join(HERE, "train_pool_r1.jsonl"), "w") as f:
    for it in out:
        f.write(json.dumps(it) + "\n")
den = sum(it["truth"] == "DENIED" for it in out)
print(f"wrote {len(out)} items ({den} DENIED); overlap with original pool verified "
      f"({sum(1 for it in out if it['id'] in orig)} shared ids, 0 divergent)")
