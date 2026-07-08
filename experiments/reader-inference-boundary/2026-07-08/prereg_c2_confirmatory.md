# Preregistration — class-c2 confirmatory (arithmetic recovery is real, not a base leak)

Fixed 2026-07-08 **after the main run, before any c2 API call**. Written because the main-run
class-c corpus has a disclosed confound (below); c2 removes it and preregisters the confirmation.

## Why c2 exists (the confound found by audit)

The main run REFUTED P-RIB-2 (recovery(c) = 0.65/0.65/0.93 for gpt/grok/haiku ≫ 0.5 guess floor;
arithmetic in capacity, P-RIB-5 pass). But a mechanical leak audit (`leak_audit.py`) found that a
**base-only heuristic** — "pick the arithmetic candidate whose stated *baseline* is already on the
fail side of its own threshold, ignoring the offset" — cleanly identifies the culprit in 41/60
class-c items, an upper bound of 0.84 recovery **with no computation**. So the main-run number
cannot by itself prove computation.

Two pieces of evidence already argue the recovery is genuine (reported as OBSERVED):
- Recovery is equal in base-**ambiguous** cells (both arith bases on the same side, heuristic must
  guess) and base-decisive cells: grok 0.64 vs 0.61, gpt 0.79 vs 0.56, haiku 0.93 vs 0.93.
- Verbose traces show explicit computation (`6 + 22 = 28`, `70 + 3 = 73`, then threshold check).

c2 converts this to a preregistered confirmation by construction.

## c2 design (base-only heuristic forced to exactly chance)

Same structure as class c (3-condition conjunctive policy, DENIED, one culprit; 1 plain non-culprit
passer + 2 arith-encoded candidates = culprit(fail) + 1 non-culprit(pass); nothing absent), with
ONE added constraint enforced by `selfcheck`:

- **Both arithmetic candidates' baselines are on the PASS side of their own thresholds.** The
  culprit crosses to a fail *only* because of its offset; the paired candidate stays passing. A
  reader that inspects only the baseline (ignoring the offset) sees two passing-looking baselines
  and cannot distinguish them — base-only recovery of the culprit is forced to 0 (must guess 1/2).
- Offset direction, magnitude, and base ordering remain balanced across items (`selfcheck` surface
  guards, |frac−0.5| ≤ 0.15) so no other first-order surface feature substitutes for computation.

N = 60 c2 items, balanced across the 6 registers, new seeds. Same three models, same WHICH /
WHICH-ABSTAIN probes, same last-anchor parser, idempotent cache, temperature 0.

## Preregistered predictions (per model; Wilson 95% CI on WHICH recovery)

- **P-C2-1 (arithmetic recovery survives leak removal):** `recovery(c2) ≥ 0.60` on ≥ 2 of 3 models.
- **P-C2-2 (recovery is above the guess floor):** `c2.ci_lower > 0.50` on the same models
  (0.50 = choosing between the two arith candidates; the plain passer is trivially excluded).
- **P-C2-3 (no residual base leak):** on the pooled c2 corpus, the base-only heuristic's culprit
  recovery ≤ 0.34 (mechanical, computed offline — a corpus property, verified in `leak_audit2`).

### Verdict logic (stated before the c2 run)

- If **P-C2-1 ∧ P-C2-2 ∧ P-C2-3** hold: the "readers only retrieve / eliminate, never compute"
  reading (a strong form of G.2) is **REFUTED at PREREGISTERED strength** — behavior-optimized
  readers deploy at least one arithmetic step of read-time justification recovery when the notes
  encode the witness as a one-step computation. This raises the ceiling on reader efficiency α
  above pure candidate-elimination.
- If recovery(c2) collapses to ≈ 0.5: the main-run c result **was** the base leak; P-RIB-2's
  original spirit (no arithmetic recovery) survives. Either way it is recorded.

## Confounds (same checklist; the base-leak is the one c2 specifically closes)

Candidate-set DISCLOSED (deployed setting, stated). Verdict/threshold language absent from notes
(selfcheck VERDICT_WORDS). Arithmetic correct and margins ≥ 15% (selfcheck). Base-only leak forced
to chance by construction and verified mechanically before scoring.

## Budget

60 items × 3 models × 2 probes = 360 calls. Hard cap 3000/model (shared runner). Est. < $0.30.
Idempotent.
