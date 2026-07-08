# Preregistration — Iterated compaction: the epistemic interest rate

Fixed 2026-07-08, **before any API call**. Corpus reuses the frozen 2026-07-06 domain-battery
DENIED items (confound-clean by construction; `experiments/lib/domains.py` selfcheck). Reader =
compressor (contract-blind), the standard protocol. Candidate-set disclosure is **irrelevant here**
(the claim is about witness *survival in the artifact*, S, measured by string check — not reader
recovery J), stated for completeness.

## The question no one has measured

Production agent memory is compacted repeatedly. Appendix H.3 found *decreasing-budget* rolling
compaction (doc→80→40→15) ≈ direct-to-15 — the terminal budget set the debt, path didn't matter,
one model. That does not answer the dynamical question: **at a FIXED budget held every round, does
witness survival decay with round number, and is the per-round survival ratio a stable constant?**
If witness survival S_r after round r follows S_r ≈ S_1 · ρ^(r−1) with ρ roughly constant, ρ is an
**epistemic interest rate** — a single dynamical number a production system could measure and
budget against. It would be the program's first *dynamical* law (everything so far is single-shot),
and the theory (Law 1 + F.4) predicts ρ < 1 (monotone decay) while the gist/verdict token persists.

## Design (fixed budget per round — the difference from H.3)

Per item: compress the ORIGINAL document to a fixed **W = 40 words**, then re-compress the summary
to 40 words again, for **R = 4 rounds** (doc→S1→S2→S3→S4), same contract-blind instruction each
round. After each round measure, from that round's summary text:
- **witness survival** S_r = mean over the 3 policy values of `retained(summary_r, value)`
  (string check — the same S as the budget-line / H.1 work);
- **failing-value survival** on DENIED items (the decision-relevant witness);
- **gist/verdict persistence** g_r = does the summary still carry the decision verdict? Measured
  two ways: (i) a decision probe on summary_r (does the reader still return the correct verdict),
  (ii) qualitative gist token via the existing `GIST_RE`;
- **realized length** L_r = word count of summary_r (the overshoot confound control).

W = 40 is chosen (not 15) specifically so that round-1 realized length has room to *plateau* near
the budget rather than collapsing below it — the H.3/J.1 lesson that a nominal budget can be
non-binding. If L_r is already ≪ W by round 1, decay would be trivially floored; the prereg guard
P-IC-0 checks the budget actually binds.

Models: grok, haiku, gpt. n = 40 DENIED items (balanced across 3 domains: ops/clinical/ci, seeds
from the existing domain corpus). temperature 0, idempotent cache keyed by (model,item,round,call),
hard cap 2000/model. Calls: 40 items × 3 models × (4 compress + 4 decision) = 960.

## Preregistered predictions (per model; survival = mean policy-value string survival)

- **P-IC-0 (budget binds — validity guard):** round-1 realized length L_1 ≥ 0.70·W (≥28 words) on
  average. If it fails, decay is confounded by a non-binding budget and the ρ estimate is reported
  as inapplicable for that model (not a pass/fail of the law).
- **P-IC-1 (monotone decay):** S_1 ≥ S_2 ≥ S_3 ≥ S_4 within tolerance 0.03 (each round no higher
  than the previous + 0.03), AND S_4 < S_1 − 0.10 (net decay over 4 rounds is real, not noise).
- **P-IC-2 (gist persists while witness decays — the shelf, dynamically):** verdict-probe accuracy
  g_4 ≥ g_1 − 0.10 (verdict roughly holds) WHILE S_4 < S_1 − 0.10 (witness falls). The gap
  (g_4 − S_4) − (g_1 − S_1) > 0 is the dynamical shelf widening.
- **P-IC-3 (stable per-round ratio — the interest rate):** the successive ratios
  ρ_r = S_(r+1)/S_r (for r where S_r ≥ 0.15, to avoid divide-by-floor noise) have
  max−min ≤ 0.20 across rounds, i.e. decay is approximately geometric with a stable ρ. Report ρ̄
  (geometric mean) per model.

### Verdict logic (stated before the run)

- **Interest rate confirmed (headline):** if P-IC-1 ∧ P-IC-2 ∧ P-IC-3 hold on ≥ 2 of 3 models
  (with P-IC-0 satisfied), then iterated compaction has a **measured, approximately stable
  per-round witness-survival ratio ρ̄** — the epistemic interest rate — while the verdict persists.
  Report ρ̄ per model and whether it is shared (cross-model constant) or model-specific.
- **Idempotence extends to fixed budget (informative null):** if P-IC-1 fails because S barely
  moves (S_4 ≥ S_1 − 0.10), then H.3's near-idempotence holds even at a fixed binding budget —
  re-compaction does not compound debt — which is a good-news null worth recording (it bounds the
  interest rate at ≈ 0).
- Any other pattern reported prediction-by-prediction; no post-hoc relabeling.

## Confound checklist (CLAUDE.md)

1. **Overshoot / non-binding budget:** the whole point-of-failure for this design. P-IC-0 guards
   it; realized L_r reported every round; W=40 chosen to bind.
2. **Last-anchor parse:** decision via `ANS_RE`; witness survival is a numeric string check
   (`retained`), not a parser-sensitive channel; UNMATCHED not applicable to S.
3. **Candidate disclosure:** N/A to S (artifact-content measure); the decision probe discloses the
   policy as usual (deployed verdict), stated.
4. **Determinism:** temperature 0, idempotent cache, seeded item selection, hard cap.

## Budget

960 calls, hard cap 2000/model. Estimated < $0.60. Idempotent — re-running is a no-op.
Smoke-test 3 items (all 4 rounds) and read the raw summaries before the full spend.
