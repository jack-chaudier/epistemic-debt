# Grok pilots — 2026-07-03

Model: `grok-4-1-fast-non-reasoning`, temperature 0, xAI API. Cumulative: 1,134 calls, ~671k tokens, ≈ $0.15. Full interpretation in [theory doc](../../../theory/justification-gap-program.md) Appendices B–E.

| ver | design | n | verdict |
|-----|--------|---|---------|
| v1 | contract-**visible** compaction (policy in doc), 80-word budget | 30 | Informative null: compressor keeps all witnesses when it knows the contract. Confounds identified: salience leak, verdict leak, citation-parsimony metric. |
| v2 | contract-**blind** (12 params, 3 secretly policy-relevant), 40-word budget | 60 | Differential shelf: DENIED (disjunctive) accuracy 0.967 survives worst retention cell; APPROVED (conjunctive) degrades with values. Missing≈failing bias; 77% confabulation on non-determinable items. CF probe non-discriminative (design flaw). |
| v3 | within-item probes: DECISION / WHICH / WHICH-ABSTAIN / REPAIR / no-notes baseline; 40w + 15w arms | 40+12 | Dissociation found (lost cell: decision 4/6, WHICH 0/6, REPAIR 1/6). Incoherence not confabulation in identification; fabrication in REPAIR 6/6. Underpowered; cross-budget confound. |
| v4 | **preregistered confirmatory**: single 15-word budget, fresh corpus, N=60, Wilson CIs, P-A..P-D fixed in advance | 60 | Replicated: WHICH retained 0.938 [0.717,0.989] vs lost 0.071 [0.013,0.315]; incoherence 12/14 vs 0/16; REPAIR fabricates 14/14; abstention 13/14 / 0 false. P-B/C/D pass; P-A floor conjunct fails informatively (always-DENY prior ⇒ bias shelf). See `v4/v4_results.json`. |

Each `vN/` contains: runner script, `items.jsonl`, `responses_raw.jsonl`, `scored.csv` (+ `summaries*.jsonl`, logs). Runners are stdlib-only, seeded, idempotent (response cache), hard call cap; API key read from environment/secret file at runtime only.
