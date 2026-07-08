# Iterated compaction — the epistemic interest rate (2026-07-08)

Preregistered: `prereg_iterated_compaction.md` (fixed before any call). New spend **$0.31**, 960
calls, 3 models. Corpus = 40 DENIED items from the frozen 2026-07-06 domain battery (ops/clinical/
ci). Fixed budget **W = 40 words**, **R = 4 rounds** (doc→S1→S2→S3→S4), same contract-blind
instruction each round; per round measure witness string-survival S_r, failing-value survival,
decision-probe verdict persistence g_r, realized length L_r.

## The question

Production agent memory is compacted repeatedly. H.3 showed *decreasing-budget* rolling compaction
(80→40→15) ≈ direct-to-15 (path didn't matter, one model). The dynamical question it left open:
**at a fixed budget every round, does witness survival decay geometrically, with a stable per-round
ratio ρ (an "epistemic interest rate")?** Law 1 + F.4 predict ρ < 1 while the verdict persists.

## Verdict: interest rate CONFIRMED on 2/3 models (grok, haiku); gpt is the near-idempotent null

| model | S₁ | S₂ | S₃ | S₄ | ρ̄ (geo-mean) | verdict g₁→g₄ | shelf widening | P-IC-0/1/2/3 |
|---|---|---|---|---|---|---|---|---|
| grok | 0.950 | 0.858 | 0.775 | 0.767 | **0.931** | 1.00→0.925 | +0.108 | ✓ ✓ ✓ ✓ |
| haiku | 0.658 | 0.575 | 0.550 | 0.542 | **0.937** | 0.85→0.875 | +0.142 | ✓ ✓ ✓ ✓ |
| gpt | 0.925 | 0.900 | 0.883 | 0.883 | 0.985 | 0.95→0.90 | −0.008 | ✓ ✗ ✗ ✓ |

Prediction-by-prediction:
- **P-IC-0 (budget binds):** PASS 3/3 — round-1 realized length 43.6 / 44.6 / 52.5 words, all
  ≥ 28 (0.70·W). The budget is not a floor artifact.
- **P-IC-1 (monotone decay, net > 0.10):** PASS grok, haiku; **FAIL gpt** (net 0.925→0.883 = 0.042
  < 0.10). gpt re-compresses near-losslessly.
- **P-IC-2 (verdict persists while witness decays):** PASS grok, haiku (verdict essentially flat
  while S falls ≥ 0.12; the shelf *widens dynamically* +0.11 / +0.14); **FAIL gpt** (no witness
  decay to accompany, so vacuously not met).
- **P-IC-3 (stable per-round ratio):** PASS 3/3 — successive-ratio spans 0.086 / 0.111 / 0.027 all
  ≤ 0.20. Decay is approximately geometric on every model that decays.

**Headline:** grok and haiku lose witnesses at a strikingly close **~6–7% per compaction round**
(ρ̄ 0.931 / 0.937) — an approximately stable, nearly cross-model geometric rate — while the verdict
survives almost unchanged. This is the program's first *dynamical* constant: the justification gap
widens monotonically with compaction rounds and the artifact drifts toward pure asserted-verdict.
gpt shows the H.3 near-idempotence extends to a fixed binding budget for models that hold summary
length steady.

## Honest confound (disclosed): realized length keeps shrinking

On grok/haiku the realized summary length *also* decays per round (grok L: 44→33→30→29; haiku
45→34→31→30) even though the 40-word budget is nominally constant — the compressor keeps
tightening below budget (the H.3 / J.1 overshoot dynamic in reverse). So ρ̄ mixes two effects:
genuine iteration loss and the summary still settling toward its stable length. gpt, which holds
length steady (~42), shows near-zero witness decay — consistent with length-settling being a large
part of the signal. **What is robust regardless:** decay is monotone and geometric (P-IC-3), the
verdict persists while witnesses fall (P-IC-2), and the two decaying models share ρ̄ ≈ 0.93. **What
needs the successor run:** a length-clamped design (force each round to *spend* the full 40 words,
e.g. reject-and-retry short summaries, or a fixed-token budget) to isolate pure per-round loss from
length settling, and more rounds (R = 6–8) to test ρ stability deeper into the chain. Labeled
accordingly: the interest rate is **PREREGISTERED-confirmed as a geometric, verdict-preserving
decay with ρ̄ ≈ 0.93 on 2 models**, and the length-settling share of that ρ is an OBSERVED caveat
for the successor to partition.

## Relation to prior results

- Extends **H.3** (near-idempotence at decreasing budgets, 1 model) to fixed budget, 3 models: the
  answer splits — near-idempotent for gpt, geometric-decay for grok/haiku.
- Instantiates **Law 1 / F.4** dynamically: witness bits are gradient-orphaned and decay under
  repeated lossy re-encoding while the answer token (defended by the decision) persists.
- The dynamical shelf widening (+0.11 / +0.14) is the single-number face of "compaction debt
  accrues interest."

## Confounds handled (CLAUDE.md)

1. Overshoot / non-binding budget: P-IC-0 guards it (passes); realized L_r reported every round and
   is itself the disclosed caveat above.
2. Parse: decision via `ANS_RE`; S is a numeric `retained()` string check (parser-insensitive).
3. Candidate disclosure: N/A to S (artifact-content measure); decision probe discloses policy as
   usual (deployed verdict), stated.
4. Determinism: temperature 0, idempotent cache keyed by (model,item,round,call), seeded item
   selection from the frozen corpus, hard cap 2000/model.

## Files

`prereg_iterated_compaction.md`, `runner.py`, `responses_raw.jsonl`,
`iterated_compaction_results.json`. Corpus reused from `experiments/domains/2026-07-06/items.jsonl`.
