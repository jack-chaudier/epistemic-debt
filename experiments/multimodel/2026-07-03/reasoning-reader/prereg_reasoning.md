# Reasoning-reader preregistration — can inference-time compute buy back artifact-borne debt?

Fixed 2026-07-03, before any reasoning-reader API call.

## Question

The transfer grid showed no fast-tier reader recovers a witness the compressor destroyed. The remaining loophole: maybe *reasoning-tier* models can — by exploiting subtle correlates in the summary (ordering, phrasing, which values were kept) that non-reasoning readers miss. Law 2 says no: the information is gone from the artifact; reasoning over a witness-free artifact is reasoning over nothing.

## Design

Answerer: **gpt-5-mini** (reasoning model, default effort; the API fixes temperature=1 — noted as a determinism caveat; single run, cached). Artifacts: grok's cached v5 summaries (applicable compressor: 22 lost / 8 retained DENIED). Probes: DECISION, WHICH, WHICH-ABSTAIN on all 60 items = 180 calls.

## Preregistered predictions

- **P-R1 (reasoning does not recover witnesses)**: `which_lost ≤ 1/3` AND `which_retained ≥ 0.7`.
- **P-R2 (reasoning improves honesty, not knowledge)**: `abstain_lost ≥ 0.5` AND `abstain_retained ≤ 0.1` — the reasoning reader detects the debt at least as well as fast readers.
- **P-R3 (the verdict shelf persists under reasoning)**: `decision_lost ≥ 0.6`.

Interpretation fixed in advance: P-R1 failure (reasoning names lost witnesses above 1/3) would be a *major* refutation — witness information would be recoverable from gist by compute, collapsing the artifact-borne-debt claim. Passes extend the claim to the reasoning tier: **inference-time compute is not a substitute for witness bits** — for context engineering this means paying for a smarter reader cannot repair a cheap compactor.

## Exploratory

Incoherence and confabulation rates vs fast-tier readers on identical artifacts; token/cost overhead of reasoning per probe.

## Budget

≤ 400 calls; cost reported.
