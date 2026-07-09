# Sections — the fail-direction fingerprint (EXPLORATORY reanalysis, 2026-07-09)

**Status: EXPLORATORY — no new API calls, no prereg yet.** Reanalysis of cached responses
(domain battery 2026-07-06; distill-parity delta battery 2026-07-08) prompted by a fresh-eyes
audit: *evidence absence never produces noise in this program's data — it produces systematic
verdicts.* Formal frame: compaction is a quotient map; on a collapsed fiber the reader emits a
learned default representative (**a section**), not "unknown". Debt is information *replaced*,
not just lost. Run `python3 reanalysis_sections.py` (deterministic, $0).

## Numbers (self-compressed artifacts; scent, not a row)

| model | DENIED-lost → approve | APPROVED-lost → deny | no-notes prior (approve, strict-anchored) | unanchored (hedge) share |
|---|---:|---:|---:|---:|
| gpt | 0.065 | 0.858 | 0.193 | 0.333 |
| haiku | 0.092 | 0.859 | 0.217 | 0.000 |
| grok | 0.330 | 0.661 | 0.000 | 0.000 |
| teacher Qwen3-8B | 0.404 | 0.562 | 0.765 | 0.837 |
| Student-V | 0.989 | **0.005** | 1.000 | 0.000 |
| Student-J | 0.820 | 0.161 | 0.986 | 0.756 |

Control cells (evidence present) approve/deny error rates are ≤ 0.05 for the frontier panel —
the section is invisible until evidence is destroyed.

## What the two added kill-checks show

1. **APPROVED-side ablation (fiber-filling vs generic conservatism):** gpt/haiku emit DENIED
   on *both* sides under evidence loss (0.86–0.94 DENIED regardless of truth) — a constant
   **fail-closed section**, directionally predictable. Student-V is the mirror: **fail-open on
   both sides** (approve 0.99 / deny 0.005). Not noise, not content-dependent filling: a
   per-model constant default.
2. **Section vs prior (is this just the bias shelf, rows 8/25?):** No — the taxonomy splits.
   *Conditional-section* models (gpt, haiku): hedgy or mild no-notes priors but decisive
   mutilation-triggered fail-closed behavior — the section only exists in the presence of an
   evidence-bearing-but-mutilated context. *Collapsed-prior* models (grok always-DENY;
   Student-V always-APPROVE): section ≈ degenerate prior pulled back — the known bias shelf.
   The 2-coordinate fingerprint (prior, section) — plus the hedge share as a third coordinate —
   distinguishes routes the ledger previously conflated.
3. **The section is trainable and sign-flippable by trace content alone:** verdict-only SFT
   turned a weak fail-closed teacher (0.40/0.56) into a hard fail-open student (0.99/0.005)
   with a degenerate always-approve prior — despite 50/50-balanced training data. Trace
   content sets the section. (Student-J stays nearer the teacher and hedges without evidence —
   its `[MISSING DATA]` register transferred to the prior channel.)

## Caveats (why this is a scent)

Self-compressed artifacts (lost cells conditioned on each model's own summaries); no
perturbation-stability arm; strict-anchor prior parse leaves 33–84% of some models' no-notes
responses unanchored (hedges — counted, not binned); the fresh-eyes haiku figure (~0.31) did
NOT reproduce under the standard lost-cell definition (we get 0.092) — definition sensitivity
is itself something the prereg must pin.

## Proposed confirmatory design (to prereg before any spend — sketch, not frozen)

Surgical-ablation corpus (delete the deciding sentence(s); no compressor — isolates the
reader's section from compaction noise and the self-compression confound), both verdict sides,
6 domains × 2 sides × ~50 items; perturbation arms (paraphrase + parameter-order shuffle) on a
subset; strict-anchored scoring with hedge shares surfaced. Predictions to freeze:

- **P-SEC-1 (existence/stability):** per frontier model, ablated-cell verdict bias ≥ 0.25 from
  coin, cross-domain spread ≤ 0.25, perturbation shift ≤ 0.10.
- **P-SEC-2 (conditionality — the anti-bias-shelf kill test):** |section − anchored prior|
  large for ≥ 2/3 frontier models; if not, D1 collapses into rows 8/25 and is reported dead.
- **P-SEC-3 (directional forecast — the money claim):** section measured on 3 domains predicts
  the *sign* of ≥ 80% of wrong answers on evidence-lost cells in 3 held-out domains + the
  cached realdoc and Arm-3b corpora (mostly reanalysis).
- **P-SEC-4 (two-route taxonomy):** grok/Student-V section ≈ own prior; gpt/haiku section ≠
  prior — preregistered per-model.

Est. cost: ~$4–6 API + $0 GPU (students scored from cache/local adapters). Theory-facing
follow-up (separate micro-design): the adaptedness/martingale frame — slide the evidence
position through the emission order and test whether verdict accuracy tracks measurability;
the already-queued forced-CoT probe on Student-V doubles as the test of whether its adapted
part still exists.
