# Evidence ledger

Status key: `THEOREM` proved · `EXACT` exhaustive computation · `PREREGISTERED` predictions fixed before run · `OBSERVED` pattern, not confirmatory · `REFUTED` · `CONJECTURE`.

| Date | Claim | Status | Evidence | Artifact |
|------|-------|--------|----------|----------|
| 2026-07-03 | `M_k = Q_(k,1)` — the witness quotient fibers over the answer quotient | THEOREM (immediate from the count formulas) | algebraic identity, cross-checked against stark sweep tables | [proofs/shelf_width_law.py](../proofs/shelf_width_law.py) |
| 2026-07-03 | Shelf Width Law: post-closure shelf width `= log2(\|Q_(k,p)\|/\|M_k\|)` | EXACT (3/3 closure families; general case CONJECTURE) | matches stark separator-closure artifacts to reported precision | same |
| 2026-07-03 | Rate-1 conservation of epistemic debt (abstention mass = debt) | REFUTED | exact partition search, 4 model families | [proofs/honesty_tax.py](../proofs/honesty_tax.py) |
| 2026-07-03 | Honesty tax: on forced-optimal layouts, converting debt to abstention destroys 2.5–18× the debt in justified answers | EXACT | same | same |
| 2026-07-03 | Honesty premium: honesty-designed layouts can certify at < 1× the debt (0.47× on causal_referee @ 2 bits); retrofit gap up to ~38× | EXACT | same | same |
| 2026-07-03 | Contract-visible compaction preserves witnesses trivially (no shelf) | OBSERVED (n=30, 1 model) | pilot v1, informative null | [experiments/.../v1](../experiments/grok-pilots/2026-07-03/v1/) |
| 2026-07-03 | Differential shelf: mirage gap appears on disjunctive (DENIED) questions, absent on conjunctive (APPROVED) | OBSERVED (v2) → PREREGISTERED-confirmed (v4, P-B) | v2 n=60; v4 P-B pass | [v2](../experiments/grok-pilots/2026-07-03/v2/) · [v4](../experiments/grok-pilots/2026-07-03/v4/v4_results.json) |
| 2026-07-03 | Within-item dissociation: verdict 0.929 vs name-the-reason 0.071 (below guessing) on lost-witness items; non-overlapping 95% CIs | PREREGISTERED (P-A accuracy conjuncts pass; 1 model) | v4 n=60, single budget, fresh corpus | [v4](../experiments/grok-pilots/2026-07-03/v4/v4_results.json) |
| 2026-07-03 | Incoherence signature: verdict `DENIED` + `PARAMETER: NONE` from same notes — 12/14 lost vs 0/16 retained | PREREGISTERED-adjacent (reported metric, replicated v3→v4; 1 model) | v3 + v4 | same |
| 2026-07-03 | Confabulation locus: identification probes honest (1/14), action probes fabricate specifics (14/14) | PREREGISTERED (P-C pass; 1 model) | v4 | same |
| 2026-07-03 | Abstention as debt detector: 13/14 uptake on lost, 0/16 false abstains | PREREGISTERED (P-D pass; 1 model) | v4 | same |
| 2026-07-03 | Lost-cell verdict accuracy is prior/gist, not knowledge (bias shelf) | OBSERVED (P-A floor conjunct failed against a degenerate always-DENY prior; needs calibrated-prior criterion) | v4 no-notes baseline | same |
| — | Law 1 (justification has no gradient), Law 3 (debt bounds transfer error), Honesty Theorem, general Shelf Width Law | CONJECTURE | theorem targets in the theory doc | [theory](../theory/justification-gap-program.md) |
