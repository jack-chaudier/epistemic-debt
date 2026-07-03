# Witness-compaction campaign — 2026-07-03

Four preregistered phases asking one question: **is the mirage shelf a hard wall, or an objective problem a better compactor can solve?** All on the v5 corpus; grok + haiku; every prereg fixed before its phase's first call; idempotent caches; temp 0. Total: ~1,900 new calls, **$0.81** (campaign), ≈ $3.00 program-to-date.

## Verdict

**The shelf is not a hard wall — it is a bit-allocation problem at the compactor.** A contract-blind compactor told to spend its budget on decision-relevant *values* instead of prose nearly reaches the contract-aware ceiling; recursive compaction does not compound the debt; and the reader is a near-perfect pass-through, so the whole exchange rate lives in the artifact. Durable long context looks achievable if (and only if) the compaction objective pays for witnesses.

## Phase A — [valuedense/](valuedense/): witness-aware blind compaction

Arms: **valuedense** (spend budget on name+number+unit readings) and **auditor** (two-pass: blind audit-list, then compress), vs realized-length-matched plain controls (prereg amendment after smoke test caught budget overshoot — the valuedense objective makes both models exceed instructed budgets; realized-length matching restores the comparison).

| model | control | retention | WHICH-denied | → arm | retention | WHICH-denied |
|---|---|---|---|---|---|---|
| grok | plain-25 (33.6w) | 0.694 | 17/30 | valuedense (31.7w) | **0.850** | **25/30** |
| grok | plain-15 (19.1w) | 0.344 | 8/30 | auditor (17.6w) | **0.600** | **14/30** |
| haiku | plain-25 (34.4w) | 0.511 | 13/30 | valuedense (43.7w)* | **0.900** | **29/30** |
| haiku | plain-15 (21.0w) | 0.339 | 11/30 | auditor (20.3w) | **0.583** | **17/30** |

**P-A1 and P-A2 pass 4/4** (retention +0.15, justified accuracy +0.15 at matched length; *haiku-valuedense overshoots its control by ~9 words — flagged; the grok comparison is clean, valuedense is *shorter* than its control and still +0.16 retention / +8 justified items). **P-A3 fails in the strong direction**: blind valuedense retention reaches 0.85–0.90 > the 0.80 "price of blindness" bound — with ~32 words of pure values, essentially the whole 12-value witness *superset* fits, so blindness costs nearly nothing once prose is evicted. **P-A4 passes** where applicable: items whose witness is still destroyed stay on the shelf (the objective moves items between cells; it rescues none in place). Exploratory: grok-auditor's decision accuracy fell 0.68→0.53 — witness-dense notes can starve the gist channel; the answer/witness trade is real but favorable.

## Phase B — [curve/](curve/): the exchange rate as a curve

grok, budgets 5→80 words, 30 DENIED items. **P-B1/B2/B3 all pass**: decision ≥ 0.83 at every budget (1.000 at 5 words — pure prior); WHICH rises monotonically 0.13→0.90, logistic midpoint ≈ **30 realized words**, shelf interval spans {5,10,15}. Sharpest exploratory fact: **WHICH ≈ failing-value survival at every budget** (max gap 0.07) — the reader is a pass-through; justified accuracy *is* witness survival. The answer curve and reason curve are flat-vs-logistic: the space between them is the quantitative picture of the shelf.

## Phase C — [recursive/](recursive/): does debt compound? (good-news refutation)

Chain doc→80→40→15 vs direct doc→15. **P-C2 and P-C3 REFUTED**: chain retention 0.367 vs direct 0.322 (no extra loss — chain was marginally *better*), decision 0.833 vs 0.867 (no corruption). Decay path 0.944→0.811→0.367: each re-compaction of an already-value-dense summary is nearly lossless; **the final budget, not the path, sets the debt.** Rolling compaction per se is not the enemy — the terminal budget is. (3 generations, one model, one protocol — labeled accordingly.)

## Phase D — [routing/](routing/): abstention as a live debt router

Cached abstention routes re-expansion to the full document. **P-D1 passes perfectly** (routed accuracy 18/18 = 1.000; router precision 1.00 — zero wasted re-expansions). **P-D2 fails by one item** (pipeline 0.867 vs always-full 1.000; criterion needed ≥ 0.90): four false-confident items answered wrong from notes without abstaining — recall 0.82; the misses are the incoherence-phenotype items. **P-D3 fails** (token ratio 0.858 vs ≤ 0.75) on this debt-heavy corpus where routing fires 60% of the time; the preregistered caveat gives the scaling: pipeline cost ≈ notes + (abstention rate) × full, so savings appear exactly when debt is rare. The primitive works; its ceiling is the router's recall, i.e., the reader's incoherent-confidence rate.

## The composite picture (Appendix H of the theory doc)

Reader efficiency ≈ 1 (B), debt set at the final compaction (C), witnesses cheap to keep once prose is evicted (A), and residual risk concentrated in false confidence (D). The road to durable long context: **value-dense contract-blind compaction + calibrated-abstention routing**, with the remaining hard problem being the incoherent-confidence failure mode — which is exactly the model-specific phenotype identified in the multimodel campaign.
