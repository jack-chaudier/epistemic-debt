# justification-gap

**A resource theory of being right for reasons.** Correctness and justification are different physical resources with a computable exchange rate. Under memory/context pressure, systems keep correct answers after losing the reasons for them (the *mirage shelf*); this repo develops the exact theory, the falsifiable laws, and the LLM experiments.

Successor / consolidation of the mirage program (`stark`, `dreams`, `mirage`, …). The theory core lives in [theory/justification-gap-program.md](theory/justification-gap-program.md).

## Results so far (2026-07-03)

| # | Result | Status | Artifact |
|---|--------|--------|----------|
| 1 | **Shelf Width Law**: `M_k = Q_(k,1)`; Q fibers over M; post-closure shelf width `= log2(\|Q\|/\|M\|)` (fiber entropy) | EXACT — verified 3/3 closure families | [proofs/shelf_width_law.py](proofs/shelf_width_law.py) |
| 2 | **Rate-1 conservation of epistemic debt** | REFUTED (exact) | [proofs/honesty_tax.py](proofs/honesty_tax.py) |
| 3 | **Honesty tax / retrofit gap**: retrofitting abstention onto answer-optimal memory costs 2.5–18× the debt; layouts designed for honesty can cost 0.47×. Faithfulness must be trained in, not bolted on | EXACT (measured on 4 model families) | [proofs/honesty_tax.py](proofs/honesty_tax.py) |
| 4 | **Within-item dissociation on Grok**: verdict survives witness destruction (0.929) while naming-the-reason collapses (0.071, below guessing); non-overlapping 95% CIs | PREREGISTERED, replicated (1 model) | [experiments/grok-pilots/2026-07-03/v4](experiments/grok-pilots/2026-07-03/v4/v4_results.json) |
| 5 | **Incoherence signature**: `DENIED` + "no failing parameter" from the same notes — 12/14 lost-witness vs 0/16 retained | PREREGISTERED, replicated (1 model) | same |
| 6 | **Confabulation locus**: identification probes stay honest (1/14 fabricated); action probes fabricate specifics 14/14 | PREREGISTERED, replicated (1 model) | same |
| 7 | **Abstention as debt detector**: 13/14 uptake on lost witnesses, 0/16 false abstains | PREREGISTERED, replicated (1 model) | same |
| 8 | The surviving verdict is prior/gist, not knowledge (**bias shelf**) — lost-cell accuracy indistinguishable from a degenerate always-DENY prior | OBSERVED (v4) → PREREGISTERED split (v5 P-E: pass grok, fail haiku — bias-shelf reading survives) | [multimodel v5](experiments/multimodel/2026-07-03/v5/v5_results.json) |
| 9 | **Cross-vendor replication**: the within-item dissociation (P-A5/B/C/D) passes preregistered on Grok AND Claude Haiku 4.5 (WHICH-lost 0/22 and 0/19); gpt-4.1-mini spontaneously implements the bare answer quotient at 15 words (retention 0.10) and shows the full pattern at 30 words (exploratory) | PREREGISTERED (2/2 applicable models) | same |
| 10 | **Debt is artifact-borne**: in all 9 compressor×answerer cells, no reader recovers a witness the compressor destroyed (WHICH-lost ≤ 0.107; retained ≥ 0.909). Compaction sets the debt of the whole pipeline | PREREGISTERED (P-T1 4/4, P-T3 2/2; P-T2 3/4, one near-miss) | [transfer](experiments/multimodel/2026-07-03/transfer/transfer_results.json) |
| 11 | **Debt phenotype is a reader property**: identical artifacts → incoherence 0.73–0.86 (grok/gpt) vs 0.00–0.05 (haiku); incoherence detectors measure reader policy, abstention-delta measures debt | OBSERVED (exploratory cells of preregistered grid); P-F incoherence itself: pass grok, fail haiku | same |
| 12 | **Loss manifests don't fix confabulation**: a contract-blind `OMITTED:` line raises abstention everywhere (→0.78/0.92/1.00) but action-channel fabrication drops only on haiku (P-M1 1/3 = FAIL); verdict unharmed (P-M2 2/3 pass) | PREREGISTERED (primary prediction failed — negative result) | [manifest](experiments/multimodel/2026-07-03/manifest/manifest_results.json) |
| 13 | **Inference-time compute can't recover artifact-borne debt**: gpt-5-mini (reasoning) names lost reasons 4/22 vs retained 8/8, abstains 20/22 vs 0/8 — a smarter reader can't repair a cheap compactor | PREREGISTERED (P-R1/R2/R3 pass) | [reasoning-reader](experiments/multimodel/2026-07-03/reasoning-reader/reasoning_results.json) |
| 14 | **Fourth vendor confirms** (gemini-3.1-flash-lite): lost-reason 3/12 vs retained 8/8, abstain 11/12 vs 0/8 — 4 vendor families, one dissociation | PREREGISTERED (P-G1/G2 pass; P-G3 unrun, free-tier) | [gemini-micro](experiments/multimodel/2026-07-03/gemini-micro/gemini_micro_results.json) |
| 15 | **The quotient identity `M_k = Q_(k,1)` does not transfer to LLM behavior**: at p=1 the logically-forced reason is named only 2/13 on lost items — reason-naming is value-retrieval, not structural inference; the empirical gap is *stronger* than the theory predicts | PREREGISTERED clean prediction REFUTED (P-S1/S3 fail; P-S2 pass) | [coarseness](experiments/multimodel/2026-07-03/coarseness/coarseness_results.json) |
| 16 | **The shelf is an objective problem, not a wall**: value-dense contract-blind compaction at matched realized length lifts justified accuracy 17/30→25/30; strict-parity auditor variant ~2× | PREREGISTERED (P-A1/A2 4/4; blindness-price bound refuted favorably) | [valuedense](experiments/witness-compaction/2026-07-03/valuedense/valuedense_results.json) |
| 17 | **Exchange-rate curve**: answer channel flat at ceiling from 5 words; reason channel logistic (midpoint ≈30 realized words); WHICH ≈ witness survival everywhere — reader efficiency ≈ 1, the artifact carries the whole exchange rate | PREREGISTERED (P-B1/B2/B3 pass) | [curve](experiments/witness-compaction/2026-07-03/curve/curve_results.json) |
| 18 | **Rolling compaction does not compound debt**: chain 80→40→15 ≈ direct-to-15; the terminal budget sets the debt, not the path | PREREGISTERED compounding prediction REFUTED — good-news null | [recursive](experiments/witness-compaction/2026-07-03/recursive/recursive_results.json) |
| 19 | **Abstention-routing loop**: router precision 1.00, re-expansion restores 18/18, end-to-end 0.27→0.87; limited exactly by incoherent-confidence misses (recall 0.82) | PREREGISTERED, split (P-D1 pass; P-D2 by one item / P-D3 fail) | [routing](experiments/witness-compaction/2026-07-03/routing/routing_results.json) |
| 20 | **Parser artifact in v5 WHICH scoring** (first-match regex dropped verbose readers' final answers as UNMATCHED); dual-judge re-score (agreement 0.974) re-identifies the reader phenotype as **calibration quality**: grok/gpt emit strong incoherence (DENIED + "nothing failed": 16/22, 24/28) while haiku emits coherent missing-data acknowledgment (15/19) — haiku natively produces the signal the loss-manifest intervention (row 12) failed to prompt in. Preregistered correctness conjuncts unaffected | EXACT (re-parse) + OBSERVED (judge re-score); corrects the row-11 mechanism | [rescore](experiments/rescore/2026-07-06/README.md) |
| 21 | **Deterministic loss-ledger routing closes the row-19 gap**: route iff a policy value is absent from the artifact (string check; deployable contract-blind via compactor-logged dropped names) — recall 1.00, precision 0.917, end-to-end 30/30 vs 26/30 reader-side | OBSERVED (re-analysis of cached routing corpus, 1 model) | [ledger re-analysis](experiments/rescore/2026-07-06/reanalysis_routing.py) |
| 22 | **Honesty premium reproduced in-repo** (`C* = solve_frontier(breach)`; 0.47×, retrofit gap 38.4×, regression-tested) + new split: premium/D > 1 on all synthetic Q families, < 1 only on the realistic causal_referee | EXACT (4 families, all budgets) | [proofs/honesty_premium.py](proofs/honesty_premium.py) |
| 23 | **Justification Budget Line (J=S, reader efficiency 1) REFUTED as universal**: 5-arm preregistered test incl. fresh clinical domain — 1/4 confirmatory arms pass (grok/clinical, slope 0.952, R² 0.995), robust to parser choice. Failure direction uniform **J ≥ S**: readers recover the witness by elimination over the probe-disclosed candidate set. Pooled J ≈ 0.92·S + 0.05 (R² 0.96); string survival is a conservative *lower bound* on justified accuracy | PREREGISTERED clean prediction REFUTED — sharper affine replacement recorded | [budgetline](experiments/laws/2026-07-03/budgetline/README.md) |

Total LLM spend to date: ≈ $4.18 (11,063 calls: $0.15 grok pilots v1–v4 + $2.04 multi-model campaign + $0.81 witness-compaction campaign + $0.08 re-score judges + $1.09 budget-line). All four provided keys produced results; a fully-billed Gemini arm (P-G3 + 360-call replications) is the only pending item (free tier = 20 req/day/model; see the multimodel campaign README).

**Campaign verdict (witness-compaction, 2026-07-03):** the shelf is an *objective problem, not a wall* — value-dense contract-blind compaction plus terminal-budget floors plus abstention-routed retrieval is a working recipe for durable long context, with incoherent confidence as the one identified failure mode still standing. See [experiments/witness-compaction/2026-07-03/](experiments/witness-compaction/2026-07-03/README.md) and theory Appendix H.

**Re-score + laws verdict (2026-07-06):** the measurement layer got audited and the theory got sharper in both directions — the reader-phenotype claim survives a parser-artifact correction but is re-identified as a calibration-quality axis (row 20); the incoherent-confidence failure mode dissolves under artifact-side ledger routing (row 21); and the clean J=S law refutes toward the safe inequality J ≥ S (row 23). See theory Appendix I.

## Quickstart

```bash
python3 proofs/shelf_width_law.py     # exact check, no dependencies
python3 proofs/honesty_tax.py         # exact check, stdlib only (~1 min)
python3 -m pytest tests/ -q           # regression + artifact integrity + secret hygiene
```

Experiments need provider keys in the environment (`XAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`) — never committed; see CLAUDE.md / AGENTS.md for hygiene rules. Re-running a completed experiment is a no-op (idempotent response caches).

## Layout

```
theory/          the program document: laws, conjectures, theorem targets, appendices A–E
proofs/          exact finite-model verifications (vendor/ = pinned copies of stark modules)
experiments/     LLM experiments; one dated dir per campaign, one vN/ per protocol iteration
results/         RESULTS.md — the evidence ledger (every claim carries a status label)
tests/           pytest: proofs stay fixed, artifacts stay intact, no secrets in tree
```

Every experiment iteration keeps: `runner*.py` (seeded, idempotent response cache, temperature 0, hard call cap), `items.jsonl`, `responses_raw.jsonl`, `scored.csv`, and for confirmatory runs a machine-readable `*_results.json` with preregistered predictions marked pass/fail.

## Roadmap

1. ~~v5 calibrated-prior criterion~~ done (split verdict — bias-shelf reading survives). ~~Multi-model replication~~ done for xAI + Anthropic (preregistered passes); add Gemini/open models when a billed key exists — runners resume idempotently.
2. **Conjunctive/disjunctive coarseness sweep** (shelf ∝ answer-quotient coarseness — the remaining quantitative theory test).
3. ~~Witness-aware compaction~~ done — the shelf bends: value-dense blind compaction ≈ contract-aware ceiling; rolling compaction doesn't compound debt; abstention-routing works to the limit of reader coherence (Appendix H). ~~Drive down the incoherent-confidence rate~~ dissolved by artifact-side ledger routing on cached data (row 21) — successor: a fresh preregistered ledger-router run (compactor actually emits the dropped-names ledger; debt-rare corpus for the cost story). Formalize the blind-vs-aware covering gap (theory).
3b. **J = S refuted → J = α·S + β** (row 23): characterize reader efficiency α per model; a candidate-blind WHICH probe to measure pure artifact content vs the disclosure-inflated deployed J; real-document corpus (external validity — everything so far is generated).
4. **Distillation experiment**: teacher vs distilled student on counterfactual variants (Law 1 at world scale).
5. Formal core: prove the Shelf Width Law in the fibered case; the Honesty Theorem; reposition the transport/holonomy material on Vorob'ev / Abramsky–Brandenburger before any external claim.

## Provenance

Exact-model machinery vendored from [`jack-chaudier/stark`](https://github.com/jack-chaudier/stark) (same author). The 2026-07-03 review of the wider mirage program and the derivation of the results above are recorded in the theory document's appendices.
