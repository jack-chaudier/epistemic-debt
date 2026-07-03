# Transfer preregistration — is epistemic debt a property of the artifact or of the reader?

Fixed 2026-07-03, before any transfer API call (v5 diagonal runs were in flight; no off-diagonal call made before this file).

## Question

v5 produces, for each of 4 compressor models, 60 contract-blind 15-word summaries of the shared corpus. Law 2 treats debt as a property of the compressed *state*: once the witness is destroyed in the artifact, no reader can recover it, and the verdict-survives / reason-collapses dissociation should hold for **every** answerer reading that artifact. The alternative (debt is reader-relative — e.g., stronger answerers extract latent witness signal, or refuse the verdict) would refute the representation-independence reading.

## Design

Grid: 4 compressors × 4 answerers over the v5 corpus. Off-diagonal cells (12) get 3 probes per item (DECISION, WHICH, WHICH-ABSTAIN) from the compressor's cached v5 summary: 12 × 60 × 3 = 2,160 calls. Diagonal cells reuse v5 verbatim. Lost/retained cells are defined by the **compressor's** summary (same tolerant matcher). Same models, temp 0, hard cap 3,000.

## Preregistered predictions

Applicability guard per (compressor, answerer) pair: compressor's cells must have n_lost ≥ 8 and n_retained ≥ 8 (compressor property, same for all answerers).

- **P-T1 (debt transfers with the artifact)**: for every applicable pair, `which_lost ≤ 1/3` AND `which_retained ≥ 0.7`. The reason channel is destroyed for all readers when the artifact loses the witness, and available to all readers when it doesn't.
- **P-T2 (the verdict shelf transfers)**: for every applicable pair, `decision_lost ≥ 0.6`. Right-without-why survives a change of reader.
- **P-T3 (no reader recovers witnesses)**: pooling over answerers, the best answerer's `which_lost` exceeds no answerer's guessing bound: max over answerers of which_lost ≤ 0.4 (evaluated per compressor). A pass means witness destruction is informational, not a decoding failure of one model family.

Campaign criterion: each of P-T1..P-T3 *holds* if it passes in ≥ 10 of 12 applicable off-diagonal pairs (T1, T2) / all applicable compressors (T3).

## Exploratory (labeled as such in the writeup)

Answerer-policy variation on identical artifacts: abstention uptake, incoherence signature rate, confabulation rate by answerer — Law 2's debt-phenotype conversion measured across model families. Compressor×answerer interaction in decision accuracy. Any post-hoc cells.

## Budget

≤ 3,000 calls this phase; token usage and dollar cost reported.
