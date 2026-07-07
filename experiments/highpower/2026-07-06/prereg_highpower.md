# Tier 1 preregistration — high-power replication of the within-item dissociation

Fixed 2026-07-06, before any API call. Corpus `items.jsonl` (seed 706010, n=400, 200 DENIED)
generated and confound-checked (clean) before this file was finalized.

## Purpose

Kill the **statistical-n** fear. The v4/v5 within-item dissociation (verdict survives witness
destruction; naming the reason collapses below guessing) was established on cells of n=14–22,
giving Wilson 95% CIs of roughly ±0.15. Here one domain (ops_incident), one budget (15 words),
one model per arm, N=400 → ≈200 DENIED → lost/retained cells near 120/80, tightening CIs to
≈±0.05. This is a precision run, not a new claim: same protocol, same corrected parser
(2026-07-06 last-anchor), 10× the items.

## Design

Reader = compressor (same model both stages), contract-blind 15-word compaction, the v5
protocol: compress → decision, which, which_abstain, repair, nonotes. Three models
(grok-4-1-fast, claude-haiku-4-5, gpt-4.1-mini). Scoring uses the corrected parser; the NONE
split here is the string heuristic (`none_missing`), with the semantic judge deferred to a
follow-up over the same raw responses.

**Probe-robustness arm (labeled, not part of the primary criterion):** variant 1 re-runs grok
with paraphrased probe wordings (compression instruction + all five probes reworded, same
semantics) on the same corpus. If the dissociation holds under variant 1, it is not an artifact
of one probe phrasing. Variant 2 available if variants 0/1 disagree.

## Preregistered predictions (per model, variant 0, Wilson 95% CIs)

- **P-H1 (dissociation)**: `which_lost` CI upper < `which_retained` CI lower (non-overlapping),
  AND `which_lost.p` < 0.34 (below 1-of-3 guessing). *Primary.*
- **P-H2 (verdict survives)**: `decision_lost.p` ≥ 0.75.
- **P-H3 (abstention detects debt)**: `abstain_lost.p` ≥ 0.60 AND `abstain_retained.p` ≤ 0.15.
- **P-H4 (confabulation locus)**: `repair_specific_lost.p` ≥ 0.60 (action channel fabricates a
  specific change) AND `which_confab_lost.p` ≤ 0.25 (identification channel does not).
- **P-H5 (prior guard, characterization not pass/fail)**: report `nonotes_deny_rate` and
  `approved_denied_under_loss`; the surviving verdict is interpreted against the always-DENY
  prior (the v4/v5 bias-shelf reading), reported, not scored.

Campaign reading: P-H1 is the headline. A model that spontaneously collapses to the bare-answer
quotient at 15 words (retention ≤ 0.15, as gpt-4.1-mini did in the multimodel campaign) is
reported **inapplicable** for P-H1/H4 (no populated lost/retained split) rather than failing,
and its retention is reported — the applicability guard from v5.

## Budget

3 models × 400 items × 6 calls = 7,200 calls (variant 0); +2,400 for the grok variant-1 arm.
Hard cap 8,000/model. Estimated < $4. Idempotent — a re-run is a no-op.
