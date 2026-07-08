# Preregistration — B5a Fusion-Contract Pilot **v2 (shelf regime, 15-word budget)**

Status: **PREREGISTERED**. Frozen 2026-07-08 before any 15-word API call (the same predictions
were first frozen in `prereg_fusion.md`'s addendum; this file is the standalone v2 spec and adds
only a *stricter* regime-applicability guard — no prediction threshold is changed).

## Why v2

v1 (`prereg_fusion.md`, 40-word nominal budget) was **non-discriminative on the primary
prediction**. The control arm never entered the shelf regime: realized words 45–58 (the
documented ~1.5× overshoot confound) so witness survival S stayed 0.78–0.98 and the number of
DENIED items that actually lost the deciding witness was only 1 / 10 / 2 (grok / haiku / gpt) of
45. With no mirage present there is no gap to collapse, so a P-FU-1 "fail" at 40w says nothing
about the hypothesis. (grok's 40w Δ was further contaminated by a WHICH abbreviation-parser
artifact — 12 UNMATCHED clinical acronyms with the witness fully surviving.)

v2 drives the compaction into the shelf regime by lowering the nominal budget to **15 words**
(exchange-rate curve: reason-channel midpoint ≈ 30 realized words; 15 nominal × ~1.5× overshoot
≈ 22 realized — real witness loss), matching the highpower/domains shelf campaigns.

## Design

Identical corpus (`items.jsonl`, 3 domains × 30 = 90), models (grok/haiku/gpt), probes
(compress → decision → which, last-anchor parser), idempotent cache, temperature 0. Only the
nominal compaction budget changes to 15 words. Arms:
- **ctrl15** — canonical contract-blind compaction, 15 words.
- **fus15** — identical + the fusion contract, 15 words.

Metrics per (model, arm): decision_acc_D, which_acc_D, S (failing-value survival on DENIED),
J (decision∧which correct), **Δ = decision_acc_D − which_acc_D**, incoherence_D
(DENIED ∧ which=NONE), realized_words, n_lost, which_unmatched_D. Candidates disclosed
(policy_text) — deployed-behavior measurement, identical across arms (see v1 prereg).

## Regime-applicability guard (new in v2)

A (model, budget) cell is **applicable** for P-FU-1 iff the **control arm loses the deciding
witness on ≥ 10 of 45 DENIED items** (`n_lost ≥ 10`). Below that there is no shelf to collapse
and P-FU-1 is reported inapplicable, not failed. Applicability is reported per model. (Applied
uniformly to v1 and v2 in the shared scorer; it makes v1 grok/gpt inapplicable, as they should
be.)

## Predictions (unchanged thresholds; frozen)

- **P-FU-1 (gap collapses).** Per applicable model: Δ(fusion) ≤ 0.5·Δ(control), with Δ(control) > 0.05.
- **P-FU-2 (no unwitnessed confidence).** Per model, route (a) incoherence_D(fusion) ≤ 0.5·incoherence_D(control),
  OR route (b) decision accuracy on lost items falls toward the no-notes prior by ≥ half the control excess.
- **P-FU-3 (length guard — collapse must not be bought with words).** Per model: realized_words(fusion) ≤ 1.25·realized_words(control).
- **P-FU-4 (witnesses survive better).** Per model: S(fusion) ≥ S(control) + 0.15.

### Anticipated (disclosed, not threshold-moving)

The v2 smoke showed the fusion contract and a 15-word budget are in **direct conflict**: told
"never claim without the value" the models keep all values and **ignore the word limit**
(realized 38–73 words vs control ~15). So P-FU-3 is expected to fail hard at 15w — the honest
reading being that fusion collapses the shelf *by refusing to compress*, i.e. it is a
witness-preservation instruction, not a free matched-budget register. Reported as the result,
not adjusted around. grok's always-DENY prior (nonotes 1.0) means route-B of P-FU-2 cannot fire
for grok and its DENIED-side Δ stays prior-driven; grok's acronym UNMATCHED artifact persists —
if UNMATCHED > 5 per arm we surface it and flag a dual-judge follow-up rather than trust the
frozen parser for the phenotype.

## Verdict rule

Hypothesis "fusion collapses the gap **by construction at a matched budget**" is supported only
if, on the applicable models, **P-FU-1 passes AND P-FU-3 holds** (collapse not bought with
length). If P-FU-1 passes only where P-FU-3 fails, the strong hypothesis is **refuted**: fusion
works as a witness-retention mechanism (P-FU-2/P-FU-4) but not for free at a fixed budget.
