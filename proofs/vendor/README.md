# vendor/

Pinned copies of three modules from `jack-chaudier/stark` (same author), vendored
2026-07-03 so the proofs in this repo are self-contained:

- `phase_transition_sweep.py` (scripts/quotient-thresholds/) — exact quotient state spaces, probe banks, causal-referee dataset
- `exact_pareto_frontier.py` (scripts/quotient-thresholds/) — partition-frontier machinery
- `unique_minimal_referee.py` (scripts/referee/) — ordered-DAG unique-minimal causal corpus

Each copy's stark-layout import block is patched to import from this directory.
Do not edit except to track upstream; new analysis code belongs in `proofs/`.
