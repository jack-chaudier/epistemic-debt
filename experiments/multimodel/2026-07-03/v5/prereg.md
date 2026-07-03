# v5 preregistration — multi-model replication of the within-item dissociation, with calibrated-prior criterion

Fixed 2026-07-03, **before** any v5 API call. Corpus: fresh seed (`Random(5151)` corpus / `Random(11000+i)` per item), N=60 (30 APPROVED, 30 DENIED with exactly one failing policy parameter, fail slots 10/10/10), same generator as v4, 15-word contract-blind compression, temperature 0, 6 calls per item per model.

## Models (fast tier, parity with grok-4-1-fast-non-reasoning)

| provider | model | config |
|---|---|---|
| xAI | grok-4-1-fast-non-reasoning | temp 0 |
| Anthropic | claude-haiku-4-5-20251001 | temp 0, max_tokens 800 |
| OpenAI | gpt-4.1-mini | temp 0 (non-reasoning) |
| Google | gemini-2.5-flash | temp 0, thinkingBudget 0, maxOutputTokens 800 |

**Amendment (2026-07-03, before any confirmatory gemini scoring):** the provided GEMINI key is free-tier with a 20-requests/day bucket for gemini-2.5-flash; the Google arm is substituted with **gemini-2.5-flash-lite** (alias `gemlite`, its own quota bucket, thinking off). Only the 3-item smoke test had run on gemini-2.5-flash; those records are ignored (different cache alias). Predictions and thresholds unchanged.

**Amendment 2 (2026-07-03, later the same day):** gemini-2.5-flash-lite is *also* capped at 20 requests/day on this key (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, quotaValue 20 — the key's project has no billing attached). The Google arm is therefore **infeasible** (needs 360 calls) and is reported as QUOTA-INFEASIBLE, not as a failure or pass. Campaign generalization criteria are evaluated over the applicable arms actually run (grok, haiku, gpt); gemlite's partial 3-item data is retained in the raw file but excluded from all confirmatory cells. If billing is attached later, the runner resumes idempotently.

Every item is compressed and probed by the **same** model (within-model condition). Cells: DENIED split by whether the failing value survives in that model's own summary (`lost` / `retained`, rounding-tolerant matcher from v3).

## Preregistered predictions (evaluated per model; a prediction *generalizes* if it passes in ≥3 of 4 models)

Applicability guard: P-A5 through P-F are evaluated for a model only if its cells satisfy n_lost ≥ 8 and n_retained ≥ 8. If a model's compressor retains too much/little, that model's run is reported as NOT-APPLICABLE with cell sizes (and any tighter-budget follow-up is exploratory).

- **P-A5 (within-item dissociation)**: `decision_lost ≥ 0.6` AND `which_lost ≤ 0.33` AND `which_retained ≥ 0.8`.
- **P-B (channel asymmetry)**: APPROVED-with-some-policy-loss decision accuracy < DENIED-lost decision accuracy.
- **P-C (confabulation locus)**: `which_confab_lost < 0.25` AND `repair_specific_lost ≥ 0.75` (identification stays honest; action probes fabricate specifics).
- **P-D (honesty uptake)**: `abstain_lost ≥ 0.5` AND `abstain_retained ≤ 0.1`.
- **P-E (calibrated-prior criterion — the v4 fix)**: balanced decision accuracy on witness-lost items exceeds the no-notes baseline's balanced accuracy by ≥ 0.10. Balanced accuracy = mean of per-class accuracy over {DENIED & failing value lost, APPROVED & any policy value lost}; the no-notes balanced accuracy is computed on the same item set. A degenerate always-DENY prior scores 0.5 on this metric, so P-E cannot be passed by bias alone. *Interpretation fixed in advance*: P-E pass ⇒ the surviving verdict carries gist (real evidential content beyond prior); P-E fail ⇒ the bias-shelf reading of v4 stands (verdict content ≈ 0 bits beyond prior) — either outcome is informative and will be reported.
- **P-F (incoherence signature, promoted from v3/v4 reported metric)**: `incoherent_lost ≥ 0.5` AND `incoherent_retained ≤ 0.1`, where incoherent = decision "DENIED" and WHICH "NONE" from the same notes.

## Not preregistered (exploratory, will be labeled as such)

Cross-model comparisons of summary length, retention rate, gist leakage; any per-domain breakdowns; anything about reasoning-tier models.

## Budget

Hard cap 2,000 calls for this phase (4 × 360 = 1,440 planned). Token usage logged from every response; cumulative dollar cost reported in the writeup.
