# Preregistration — B5a Fusion-Contract Pilot (2026-07-08)

Status: **PREREGISTERED**. Predictions and thresholds below are frozen before any API call.
Refutation is a result: every prediction is reported pass/fail, including awkward failures.

## Hypothesis

The mirage shelf (verdict survives compaction while the deciding witness dies, so decision
accuracy ≫ WHICH accuracy) exists because the verdict-bearing gist and the witness value are
**separable strings** in the compacted artifact — a contract-blind compactor keeps an
evaluative gist and drops the number. A **fusion contract** on the compactor — "you may never
state an evaluative or verdict-bearing claim without the specific deciding value in the same
clause; if you cannot afford the value, drop the claim entirely" — makes gist and witness
survive or die together. Prediction: the answer/justification gap Δ collapses *by construction*
(theory §5.1 as a prose register).

## Design

- **Two arms, matched nominal budget = 40 words** (consistent with the iterated-compaction and
  witness-compaction campaigns; realized words recorded and guarded, see P-FU-3):
  - **CONTROL** — the canonical contract-blind compaction instruction used in every prior
    dissociation campaign (COMPRESS_SYS[0] wording), budget 40 words.
  - **FUSION** — identical instruction + budget, plus the fusion-contract sentences.
- **Corpus**: `items.jsonl` — 3 confound-guarded domains (ops_incident, clinical_enroll,
  ci_release) × 30 items = 90 (45 DENIED / 45 APPROVED), from `experiments/lib/domains.py`.
  Mechanical selfcheck passes with 0 problems (salience / verdict-leak / value-collision).
- **Models**: grok (`grok-4-1-fast-non-reasoning`), haiku (`claude-haiku-4-5`),
  gpt (`gpt-4.1-mini`), via `experiments/multimodel/2026-07-03/providers.py`. Temperature 0.
- **Probes per item per arm**: `compress` (arm-specific system) → `decision` (APPROVED/DENIED
  under the disclosed policy) → `which` (name the single failing parameter, last-anchor parser).
  Plus one arm-independent `nonotes` probe per item (policy only, no notes) for the prior.
- Idempotent cache keyed by (model, item, call); temperature 0; hard call cap 3000/model.

### Metrics (per model, per arm)

- **decision_acc** = P(decision == truth) over all 90 items; **decision_acc_D** over the 45 DENIED.
- **which_acc_D** = P(which == failing_param) over the 45 DENIED (corrected last-`PARAMETER:`
  parser; UNMATCHED surfaced, never binned).
- **S** = failing-value string survival on DENIED items = P(failing value appears in summary).
  Reported alongside policy-value survival (mean of the 3 policy values).
- **J** (justified accuracy) = P(decision correct AND which correct) over DENIED items.
- **Δ = decision_acc_D − which_acc_D** — the headline answer/justification gap.
- **incoherence_D** = P(decision == DENIED AND which ∈ {NONE}) over DENIED items — verdict
  asserted with no nameable reason (the mirage signature).
- **realized_words** = mean word count of the `compress` output.
- **lost subset** = DENIED items whose failing value is absent from the summary (per arm);
  incoherence and decision accuracy also reported on this subset for the mechanism read.

### Candidate-set disclosure (confound #3, stated per CLAUDE.md)

The `which` probe **discloses the candidate set**: `policy_text` names the 3 policy parameters,
so a reader can recover the failing one by elimination and which_acc can exceed string survival
S (J ≥ S). This is deliberate — we measure **deployed reader behavior** (the reader always has
the policy), not artifact-content-only recovery. Disclosure is identical across both arms, so
it cannot manufacture a between-arm Δ difference. Reported: which_acc may sit above S in both
arms; the between-arm *contrast* is the inference.

## Predictions (frozen thresholds)

- **P-FU-1 (gap collapses).** Per model: Δ(fusion) ≤ 0.5 · Δ(control). Pass iff Δ(control) > 0
  and the halving holds. (If Δ(control) ≈ 0 for a model, that model is inapplicable — no shelf
  to collapse — and is reported as such, not counted pass or fail.)
- **P-FU-2 (no unwitnessed confidence).** Per model, EITHER route:
  (a) incoherence_D(fusion) ≤ 0.5 · incoherence_D(control) — the mirage signature at least
  halved; OR (b) on lost-witness items the fusion arm's decision accuracy falls toward the
  no-notes prior: decision_acc(fusion-lost) − nonotes_deny_rate ≤ 0.5 · [decision_acc(control-lost)
  − nonotes_deny_rate]. Pass iff (a) OR (b).
- **P-FU-3 (length guard — the contract must not just buy the gap with words).** Per model:
  realized_words(fusion) ≤ 1.25 · realized_words(control).
- **P-FU-4 (witnesses survive better).** Per model: S(fusion) ≥ S(control) + 0.15.

### Verdict rule

- "Fusion collapses the gap **by construction**" is supported iff **P-FU-1 passes on ≥ 2 of 3
  applicable models AND P-FU-3 holds on those models** (the collapse is not bought with length).
- P-FU-2 and P-FU-4 identify *which mechanism route* produced the collapse (witness survival
  rises, route B / P-FU-4; or unwitnessed confidence is suppressed, route A / P-FU-2). At least
  one should fire on each model where P-FU-1 passes; if P-FU-1 passes but neither P-FU-2 nor
  P-FU-4 does, that is an anomaly to explain (e.g., elimination inflating which_acc).
- Any model where fusion fails to collapse Δ is reported prominently as a **refutation** for
  that model — the fusion register is not a universal fix.

## Smoke gate (before full spend)

3 items × 3 models × both arms, raw outputs inspected for: (i) FUSION actually produces fused
clauses (evaluative claim + value together, or bare values, never bare gist); (ii) CONTROL
retains the naked-gist capability (so there is a shelf to collapse); (iii) no probe leaks the
candidate set beyond the disclosed policy_text; (iv) realized lengths are in range. Full run
only if the fusion instruction visibly changes the compaction register.

## Cost

Est. ≤ 90 items × (3 arm-probes × 2 arms + 1 nonotes) = 630 calls/model × 3 = 1,890 calls.
Prior comparable runs ≈ $0.9. Hard budget cap **$5**.

---

## Addendum — tight-budget (15-word) condition (frozen 2026-07-08, before its calls)

**Why.** The 40-word run (completed) revealed a **budget confound**: at 40 words the compactor
retains essentially all 12 short numeric readings, so witness survival S is already 0.78–0.98 in
control — there is almost no mirage shelf to collapse. The residual gap on grok is a WHICH
abbreviation-parser artifact (SBP/CrCl/LVEF → UNMATCHED with the failing value fully surviving),
not witness loss. The hypothesis (fusion collapses the mirage) therefore cannot be tested at 40w
because the mirage is absent. The prior shelf campaigns (highpower/domains) used **15 words** to
create the shelf; I add a matched-15w condition to test fusion where a real shelf exists.

- **New arms, matched nominal budget = 15 words**: `ctrl15` (canonical contract-blind, 15w) and
  `fus15` (same + identical fusion contract, 15w). Same corpus, models, probes, parser, cache
  (new call keys `*_15`; the 40w cache is untouched). `nonotes` is reused (budget-independent).
- **Predictions**: the same P-FU-1…P-FU-4 with the same thresholds, evaluated on the 15w arms.
  All frozen before any 15w call. The 15w condition is the primary test of the hypothesis; the
  40w condition is reported as an informative budget-dependence result.
- **Anticipated wrinkle (not a moving threshold, just disclosed):** grok's no-notes prior is
  degenerate always-DENY (nonotes_deny 1.0), so on DENIED items its decision accuracy stays high
  even with zero information — route-B of P-FU-2 cannot fire for grok and its DENIED-side Δ is
  prior-driven, not knowledge-driven (the P-E bias-shelf caveat). grok's WHICH parser artifact
  (acronyms) also persists at 15w. So grok is expected to be an unreliable P-FU-1 vehicle under
  the frozen parser regardless of fusion; haiku/gpt are the clean tests. Reported, not adjusted.
