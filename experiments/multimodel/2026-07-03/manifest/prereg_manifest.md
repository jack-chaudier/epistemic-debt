# Manifest preregistration — does a loss ledger at compaction time defuse action-channel confabulation?

Fixed 2026-07-03, before any manifest-phase API call.

## Motivation

v4 (and, expected, v5) locate confabulation in the *action* channel: on lost-witness items, models fabricate specific repair actions (grok: 14/14) even while identification probes stay honest. The theory-doc §7 proposes an accounting discipline for epistemic debt: compaction should emit what it dropped. This phase tests the cheapest possible version — one extra manifest line, still fully contract-blind — as a context-engineering intervention.

## Design

Same v5 corpus (60 items), same models, temp 0. Two compression arms at **equal 25-word total budget**:

- **plain25**: v5 compression prompt with a 25-word limit.
- **manifest**: 15-word notes, plus one line `OMITTED: <kinds of information dropped>` of at most 10 words. Same contract-blind framing.

Probes per arm from the arm's own summary: DECISION, WHICH, WHICH-ABSTAIN, REPAIR. 60×(1+4)=300 calls per model per arm. Models: grok, gpt, haiku; gemini contingent on quota (rate-limited; included if feasible). Lost/retained cells per arm's own summaries (numeric matcher; the OMITTED line contains no parameter values, so it cannot fake retention).

## Preregistered predictions (per model; applicability: n_lost ≥ 8 in both arms)

- **P-M1 (fabrication drops)**: `repair_specific_lost(manifest) ≤ repair_specific_lost(plain25) − 0.30`. The loss ledger licenses the model to say "cannot determine" in the action channel.
- **P-M2 (the verdict is free)**: overall decision accuracy in the manifest arm ≥ plain25 arm − 0.10. The manifest spends 10 of 25 words on meta-information; the prediction is that this costs (almost) nothing on the answer channel, because the verdict rides on gist, not on the dropped values.

Campaign criterion: each prediction generalizes if it passes in every applicable model minus at most one.

## Exploratory

Abstention uptake shift (may be at ceiling), incoherence rate, which-channel accuracy changes, retention differences between arms (manifest has 10 fewer note words — retention in the manifest arm is expected *lower*; this works against P-M2, making a pass more informative), qualitative manifest content.

## Budget

≤ 3,000 calls this phase; cost reported.
