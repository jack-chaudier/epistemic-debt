# Coarseness sweep preregistration — the reason-channel gap should track the witness-fiber size

Fixed 2026-07-03, before any coarseness API call.

## Theory being tested (Shelf Width Law, LLM-scale shadow)

`M_k = Q_(k,1)`: with a **single-condition policy** (p=1), the answer quotient and the witness quotient coincide — the verdict logically determines the reason, so destroying the witness *value* in the summary should not touch the ability to name the failing parameter. With a **six-condition policy** (p=6), the verdict leaves a 6-way witness fiber; witness loss should crash reason-naming toward 1/6 guessing. Same compressor, same budget, same probes — only the quotient structure moves.

## Design

Two fresh 30-item arms (24 DENIED with exactly one failing parameter, 6 APPROVED catch items), generator as v5 but with 1 (resp. 6) policy conditions drawn from the same 12-parameter pools; seeds `Random(6161+arm)` corpus / `Random(13000+i)`, `Random(15000+i)` per item. Model: grok-4-1-fast-non-reasoning (cheapest replicated baseline), temp 0. Per item: COMPRESS (15-word contract-blind), DECISION, WHICH, WHICH-ABSTAIN = 240 calls. Cells by failing-value retention in the arm's own summaries; applicability n_lost ≥ 8 per arm.

## Preregistered predictions

- **P-S1 (fiber of size 1 ⇒ no reason gap)**: `which_lost(p=1) ≥ 0.8`.
- **P-S2 (fiber of size 6 ⇒ reason gap at guessing)**: `which_lost(p=6) ≤ 1/3`.
- **P-S3 (abstention tracks the fiber, not the missing evidence)**: `abstain_lost(p=1) ≤ 0.25` AND `abstain_lost(p=6) ≥ 0.5`. With p=1 the reason is deducible without the evidence, so an honest reader should answer, not abstain; with p=6 it cannot be deduced, so it should abstain.

Interpretation fixed in advance: P-S1 failure would mean the reason channel collapses even when the witness is logically recoverable from the verdict — i.e., the shelf is a probe artifact, not quotient structure (against the theory). P-S2/P-S3 failures in the other direction would mean readers extract witness identity without the value (also against the theory). Passes make the reason-channel gap a *function of answer-quotient coarseness*, which is the Shelf Width Law's qualitative LLM shadow.

## Exploratory

decision accuracy by arm; retention by arm (6 values are harder to keep in 15 words — expected); incoherence; APPROVED catch-trial behavior.

## Budget

≤ 400 calls, grok only; cost reported.
