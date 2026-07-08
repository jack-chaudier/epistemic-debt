# Preregistration — Real-document external-validity tier (2026-07-08)

**Status: FROZEN 2026-07-08 after the 3-item × 2-model smoke (items 000–002, cached; budget line
confirmed below). No full-run probe call precedes this freeze.** Queue item 7 (NEXT.md): every result
so far lives on synthetic policy documents; this run tests whether the answer/justification
dissociation — and the fusion fix — survive **real prose**.

## Method — semi-synthetic injection

Real public-domain narratives (US NTSB aviation-accident *Analysis* sections; provenance in
`SOURCES.md`) with 3 decision-relevant policy readings injected into the natural prose at varied
positions (`gen_items.py`). Ground truth fully controlled (verdict = conjunction of 3 injected
thresholds, balanced APPROVED/DENIED, exactly one failing parameter when DENIED); linguistic texture
real. **12 sources × 5 policy variants = 60 items** (30 APPROVED / 30 DENIED). Framing: an
airworthiness / return-to-service review file; the accident narrative is the occurrence summary
(texture + distractor numerals), the injected readings are investigation/maintenance findings in the
register NTSB analyses already use.

**Key design property (why the real prose cannot leak the verdict).** Each source appears 5× with
different injected values and a balanced verdict, so the narrative's dramatic gist is *decorrelated
from truth by construction*. Any "crash → DENY" bias from the accident outcome is therefore a uniform
confound on decision accuracy (measured via APPROVED-side accuracy and the nonotes prior), **not** a
channel that manufactures the answer/justification gap.

## Design

- **Arms (matched budget):** CONTROL = canonical contract-blind compaction (signpost-fusion
  `COMPRESS_SYS[0]`); FUSION = same + the exact fusion contract from `signpost-fusion/runner.py`
  (never state an evaluative claim without its deciding value in the same clause).
- **Models:** haiku (`claude-haiku-4-5`), gpt (`gpt-4.1-mini`) — the clean-parser models. grok
  skipped (WHICH acronym-parser artifact, confound #2, would need a semantic dual-judge).
- **Probes:** decision (APPROVED/DENIED), WHICH (corrected last-`PARAMETER:` parser), nonotes prior.
- **Budget:** fixed **nominal 15 words** on every item — the shelf regime from signpost-fusion (v2),
  and a realistic deployed-compactor spec (fixed budget regardless of input length). Realized length
  measured and disclosed per arm (the known fusion budget-override; **not** a prediction). *Confirmed
  by smoke (items 000–002, haiku+gpt): at 15w the CONTROL compactor summarizes the accident gist to
  ~17–19 realized words and drops every injected reading (S→~0), so the shelf forms; it does not scale
  to document length. Budget line frozen as-is — no amendment needed.*
- **Regime-applicability guard:** a model's dissociation predictions apply only if the CONTROL arm
  actually destroys the deciding witness on **≥ 10 of its DENIED items** (`n_lost ≥ 10`). A budget
  where witnesses survive has no mirage to collapse.

Candidate set **disclosed** (policy_text lists the 3 params) — deployed-behavior measurement,
identical across arms; so WHICH ≥ S by elimination in both arms (cannot manufacture a between-arm
contrast). Temperature 0, idempotent cache, hard cap 2000/model, cost logged. Budget cap **$8**.

## Predictions (pass/fail, per model, given the regime guard)

- **P-RD-1 — the dissociation replicates on real prose.** CONTROL Δ = decision_acc(DENIED) −
  WHICH_acc(DENIED) **≥ 0.20** for each applicable model. *Preregistered caveat (from smoke): on real
  accident narratives the surviving "answer" is the crash-outcome gist (control returns DENIED even on
  APPROVED items), so DENIED-side decision accuracy is inflated by a crash→DENY bias. Δ ≥ 0.20 is a
  necessary but not sufficient signal; it is read together with decision_acc(APPROVED) and the nonotes
  prior. A large Δ with low APPROVED-side accuracy means the answer channel that survives is the
  narrative gist, not a policy verdict — an even sharper external-validity failure than the synthetic
  shelf, not a weaker one.*
- **P-RD-2 — incoherence appears.** CONTROL incoherence_D (DENIED asserted with `PARAMETER: NONE`)
  **≥ 0.05** for each applicable model.
- **P-RD-3 — fusion still kills it.** FUSION incoherence_D **≤ 0.5 × CONTROL** incoherence_D (expect
  → 0), where CONTROL incoherence_D > 0.
- **P-RD-4 — witness-survival lift.** S(FUSION) **≥ S(CONTROL) + 0.15**, where S = failing-value
  survival on DENIED items.

**Disclosed measurement (not a prediction):** realized-length ratio rlzW(FUSION) / rlzW(CONTROL) —
the known fusion budget-override from signpost-fusion (1.7–1.9× at 15w). Reported per model.

## Confound checklist (carried forward + new)

1. **Value-collision with source numerals (NEW — the real-doc confound).** Injected values are drawn
   to be UNIQUELY `retained()` among all numerals in the final document (source narrative numbers +
   the 3 injected); the failing value in particular is a unique string. Mechanically enforced by
   `gen_items.selfcheck` (must report 0 problems before the run).
2. **Injected-sentence verdict leak.** The 3 injected findings are scanned with `domains.VERDICT_WORDS`;
   the real narrative is **not** scrubbed (uncontrolled real prose about a different subject, and
   decorrelated from truth — see the design property above).
3. **Accident-outcome gist bias (disclosed).** Real narratives carry outcome language ("substantial
   damage", "in-flight breakup"). Decorrelated from truth by the 5-variant construction; any bias
   surfaces as depressed APPROVED-side accuracy / elevated nonotes-deny prior, both reported.
4. **Candidate-set disclosure (#3).** policy_text discloses the 3 candidates; identical across arms.
5. **Parser artifact (#2).** grok excluded; haiku/gpt use the corrected last-anchor parser; WHICH
   UNMATCHED count surfaced per arm (never binned).

## Verdict rule

External validity is **upheld** if P-RD-1 and P-RD-2 pass on ≥ 1 applicable model (the shelf transfers
to real prose) and the fusion mechanism (P-RD-3/P-RD-4) reproduces. A **negative** result — the shelf
does not form on real prose (P-RD-1/2 fail with the regime guard satisfied, or the guard is never
satisfied because witnesses survive) — is reported with full prominence: it would bound every
production claim in the roadmap.
