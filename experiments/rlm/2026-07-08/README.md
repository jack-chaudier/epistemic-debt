# R1 — Δ-audit of vanilla RLM (STUB — build paused 2026-07-08)

**Status: harness partially built; NO preregistration frozen, no results.** A handful of
pre-smoke probe calls (30 lines in `responses_raw.jsonl`, pennies of spend) were cached before
the build was paused — they are exploratory smoke output, not data. Nothing here is citable.
The full R1 charter (design, preregistered predictions, confound guards, budget) is in
[`../SCOPE.md`](../SCOPE.md).

Contents so far: `gen_items.py` (long-context item generator over the ledger corpora),
`items.jsonl`, `rlm_loop.py` (minimal seeded/cached recursion loop), and the smoke cache.
Resume by re-reading SCOPE.md §R1: smoke 3 items per condition, inspect raw traces, freeze
`prereg_rlm_audit.md`, then run.
