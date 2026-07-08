#!/usr/bin/env python3
"""Fixed probe slice for the J-prompt revision protocol: 500 items (250/250 by verdict),
seeded sample (813000) of the G2-kept 5 domains of train_pool.jsonl. The SAME slice evaluates
every revision (revision_protocol.md rule 2). Deterministic; writes probe_slice.jsonl."""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 813000
KEPT = {"ci_release", "clinical_enroll", "loan_underwrite", "sec_triage", "vendor_sla"}

items = [json.loads(l) for l in open(os.path.join(HERE, "train_pool.jsonl"))
         if json.loads(l)["domain"] in KEPT]
rng = random.Random(SEED)
app = [it for it in items if it["truth"] == "APPROVED"]
den = [it for it in items if it["truth"] == "DENIED"]
slice_ = rng.sample(app, 250) + rng.sample(den, 250)
rng.shuffle(slice_)
with open(os.path.join(HERE, "probe_slice.jsonl"), "w") as f:
    for it in slice_:
        f.write(json.dumps(it) + "\n")
print(f"wrote {len(slice_)} probe items "
      f"({sum(it['truth'] == 'DENIED' for it in slice_)} DENIED, seed {SEED})")
