# Preregistration — B1 Certificate-Compaction Pilot (2026-07-08)

Status: **PREREGISTERED**. Predictions and thresholds below are frozen before the full run.
The corpus, all four arm prompts, the parser, and every threshold are fixed here; smoke (6
items × 3 models × 4 arms) was inspected only to confirm the format renders as designed (see
"Smoke gate" — the writer/reader phenotypes observed there are *results*, not tuning targets).
Refutation is a result: every prediction is reported pass/fail, including awkward failures.

## Hypothesis

The Honesty Theorem exact check (`proofs/honesty_theorem.py`, RESULTS row 13) found that
**certificate honesty admits a strictly cheaper state than exact-witness honesty** on the Q
families (answer / certificate / joint states 5/6/7, 6/7/8, **7/9/13** on `Q_(5,3)`): to answer
honestly you need only preserve enough to certify the answer (one deciding witness + the fact
that it certifies), not the full witness set.

LLM analog. A compaction format of **claim + minimal certificate + pointer** — e.g.
`"DENIED. seal torque 60.86 N·m vs 81.6 threshold. Other readings not included — see source."` —
should license calibrated reader behaviour (correct verdict + correct reason-naming + abstention
when the certificate is absent) at **fewer realized words** than value-dense compaction, which
stores the whole witness set (all candidate readings). Certificates store only the deciding value
+ a pointer; value-dense stores everything.

The theory predicts an **asymmetry** we carry as a stated expectation, not a moving threshold:
certificate honesty is cheap on the *certifiable* side ("any surviving witness certifies
feasible" — our **DENIED** items, where one failing reading certifies denial) but not on the
universally-quantified side (**APPROVED**, which requires *all* criteria met — no single-object
certificate). We therefore expect the certificate advantage to be real on the DENIED side and to
strain on the APPROVED side.

## Design

Four compaction arms, matched **15-word nominal budget** (the shelf regime of the highpower /
domains / signpost-fusion campaigns; realized words recorded and guarded, see P-CE-4):

- **CONTROL (`ctrl`)** — canonical contract-blind plain compaction (the wording used in every
  prior dissociation campaign). **Policy-blind** (sees the record only).
- **VALUEDENSE (`vd`)** — the H.2 names+numbers+units instruction (verbatim design from
  `experiments/witness-compaction/2026-07-03/valuedense/`). **Policy-blind**. The deployed
  value-dense baseline.
- **VALUEDENSE_AWARE (`vda`)** — same value-density goal, but the writer **holds the policy**
  ("keep the policy-relevant readings so any threshold question can be answered"). The
  **matched-policy-access** control that isolates *format* from *policy access* for the
  certificate-quotient claim (value-dense = store the whole witness set / joint quotient).
- **CERTIFICATE (`cert`)** — **policy-aware** cooperative writer: a terse certificate =
  (1) the decision the policy reaches; (2) for DENIED, only the single failing reading as
  `name number unit vs threshold`; for APPROVED, `all criteria met`; (3) a pointer
  `other readings not included — see source`. The certificate quotient: store the deciding value
  + a pointer, not the full set.

A certificate must name the *deciding* reading, which requires the policy — so `cert` and `vda`
are policy-aware and `ctrl`/`vd` are the blind deployed baselines. **Policy access is a disclosed
design axis, not a nuisance**: P-CE-1 (certificate quotient) is scored against `vda` at *matched*
access; P-CE-1b reports the team-lead literal comparison against blind `vd`.

- **Corpus**: `items.jsonl` — 3 confound-guarded domains (ops_incident, clinical_enroll,
  ci_release) × 30 = 90 items (45 DENIED / 45 APPROVED), from `experiments/lib/domains.py`, same
  generator + seeds (BASE_SEED 20260708) as the signpost-fusion pilot. Mechanical selfcheck
  passes with 0 problems (salience / verdict-leak / value-collision).
- **Models**: grok (`grok-4-1-fast-non-reasoning`), haiku (`claude-haiku-4-5`),
  gpt (`gpt-4.1-mini`), via `providers.py`. Temperature 0. grok's WHICH abbreviation-parser
  artifact (confound #2) is documented; grok is reported but flagged — haiku/gpt are the clean
  tests.
- **Probes per item per arm**: `compress` (arm-specific) → `decision` (APPROVED/DENIED under the
  disclosed policy) → `which` (name the single failing parameter) → `which_abstain` (same, with
  an explicit `PARAMETER: INSUFFICIENT_EVIDENCE` option — calibration is the point of
  certificates). Plus one arm-independent `nonotes` probe/item (policy only) for the prior.
- Idempotent cache keyed by (model, item, call); temperature 0; hard call cap 3000/model.

### Metrics (per model, per arm)

- **decision_acc** = P(decision == truth) over all 90 items; **decision_acc_D** over 45 DENIED.
- **which_acc_D** = P(which == failing_param) over the 45 DENIED (corrected last-`PARAMETER:`
  parser; UNMATCHED surfaced, never binned).
- **S** = failing-value string survival on DENIED = P(failing value appears in the summary).
- **J** (justified accuracy) = P(decision correct AND which correct) over DENIED items. The
  headline economy metric — *note J is DENIED-only by construction*; APPROVED-side behaviour is
  read from the abstention-calibration cells below and from decision_acc.
- **realized_words** = mean word count of the `compress` output (the economy axis).
- **Δ = decision_acc_D − which_acc_D** — the answer/justification gap (reported for continuity).
- **incoherence_D** = P(decision == DENIED AND which == NONE) over DENIED — the mirage signature.
- **Abstention calibration (from `which_abstain`)**: on APPROVED items, `approved_none` =
  P(says NONE, correct); `approved_false_abstain` = P(says INSUFFICIENT_EVIDENCE, wrong);
  `approved_confab` = P(names a parameter, wrong). On DENIED-lost items, `lost_abstain` =
  P(abstains, the *calibrated* response when the witness is gone).

### Candidate-set disclosure (confound #3, stated per CLAUDE.md)

The `which`/`which_abstain` probes **disclose the candidate set** (`policy_text` names the 3
policy parameters), so a reader can recover the failing one by elimination and which_acc can
exceed S (J ≥ S). Deliberate — we measure **deployed reader behaviour** (the reader always holds
the policy). Disclosure is identical across all four arms, so it cannot manufacture a between-arm
contrast; the between-arm difference is the inference.

## Predictions (frozen thresholds)

- **P-CE-1 (certificate quotient — matched policy access).** Per model:
  `J(cert) ≥ J(vda) − 0.05` (non-inferior justified accuracy) **AND**
  `realized_words(cert) < realized_words(vda)` (strictly fewer words). The clean 9-vs-13 analog:
  same licensed behaviour, cheaper state.
- **P-CE-1b (vs blind value-dense — team-lead literal).** Per model:
  `J(cert) ≥ J(vd) − 0.05` **AND** `realized_words(cert) ≤ realized_words(vd)`.
- **P-CE-2 (abstention calibrated on APPROVED).** Per model, certificate arm:
  `approved_false_abstain ≤ 0.10` **AND** `approved_none ≥ 0.90`. (This is the theory's
  hard side — a value-free approval certificate may force the reader to over-abstain, or a
  writer miscomputation may false-deny. Either failure is the predicted asymmetry, reported.)
- **P-CE-3 (beats control on J in the shelf regime).** Per model, applicable iff CONTROL is in
  the shelf regime (`ctrl n_lost ≥ 10` of 45 DENIED): `J(cert) − J(ctrl) ≥ 0.20`.
- **P-CE-4 (word economy — the core economy claim, and the signpost-fusion length guard).**
  Per model: `realized_words(cert) ≤ realized_words(vd)` **AND** `≤ realized_words(vda)`. The
  signpost-fusion lesson (a witness-preserving contract can *override* the budget) is guarded
  here: if the certificate buys behaviour with words it fails P-CE-4. Realized-length ratios are
  reported prominently for all arms.

### Verdict rule

- The **certificate quotient transfers** iff **P-CE-1 passes on ≥ 2 of 3 models AND P-CE-4 holds
  on those models** (cheaper words, non-inferior J — not bought with length).
- **P-CE-2** is the asymmetry test: it is *expected* to strain on the APPROVED side. Report per
  model *why* it passes/fails (reader over-abstention vs writer false-denial), since the theory
  predicts the APPROVED side has no cheap certificate.
- **P-CE-3** establishes the certificate format beats naive compaction where a real shelf exists.
- Any model where the certificate fails to be both cheaper and non-inferior is reported
  prominently as a **refutation** for that model.

## Smoke gate (done — 6 items × 3 models × 4 arms, inspected before freezing)

Confirmed: (i) the certificate arm renders as claim + single-value certificate + pointer, terse
(11–19 realized words) — the cheapest arm (cert < vda < vd < ctrl); (ii) readers parse the
certificate cleanly on DENIED (verdict + correct parameter); (iii) the predicted asymmetry is
visible on APPROVED — haiku's reader **over-abstains** on a value-free approval certificate, and
grok/gpt **writers false-deny** a passing item (ops-004: reserve margin 76.53 ≥ 74 min, both
wrote DENIED). These are recorded as the phenomena the full run will quantify, **not** tuned away:
the certificate prompt is frozen as smoked. Full run proceeds.

## Cost

Est. 90 items × (4 arms × 4 probes + 1 nonotes) = 1,530 calls/model × 3 ≈ 4,590 calls. Prior
comparable runs ≈ $1.6–3. Hard budget cap **$6**.
