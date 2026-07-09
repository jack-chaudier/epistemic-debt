# Preregistration — Sections campaign (freeze on commit, before any API spend)

Claim under test (D1, from the 2026-07-09 exploratory reanalysis): when the deciding evidence
is destroyed, a model emits a characteristic default verdict — a **section** — that is (1) a
stable model property, (2) distinct from its no-notes prior for at least part of the frontier
panel (i.e., NOT the bias shelf of rows 8/25), and (3) predictive of the *direction* of unseen
silent failures. Corpus: surgical ablation (`gen_items.py`, seed family 814xxx), 6 domains × 60
items (30/30 by verdict), no compressor — isolating the reader's section from compaction noise
and from the self-compression confound in the exploratory numbers. Models: grok / haiku / gpt
(providers.py aliases), temperature 0, idempotent cache, hard cap, strict last-`ANSWER:`-anchor
parsing with unanchored (hedge) shares surfaced, never binned.

## Probes (per item per model)

`nonotes` (policy only), `ctrl_decision` (intact doc), `abl_decision` (ablated doc),
`abl_abstain` (ablated doc + explicit INSUFFICIENT_EVIDENCE option); perturbation arms on the
first two domains: `abl_shuffle` (sentence-order reshuffle) and `abl_reword` (probe variant-1
wording). ≈ 5,040 calls, est. $3–5.

## Definitions (frozen)

- **Section (per model):** on ablated cells pooled across sides, the majority verdict among
  anchored answers; **section strength** = that majority's rate. Per-side biases reported
  (DENIED-ablated approve-rate; APPROVED-ablated deny-rate).
- **Hedge coordinate:** unanchored share on `abl_decision` + abstain rate on `abl_abstain`.
- **Prior:** anchored `nonotes` approve-rate; unanchored share reported.
- **Error sign:** an incorrect anchored decision is APPROVE-signed or DENY-signed by its
  emitted verdict.

## Predictions (each reported pass/fail)

- **P-SEC-1 (existence + stability), per model:** (a) section strength ≥ 0.75; (b) per-domain
  section-strength range ≤ 0.25; (c) perturbation shifts ≤ 0.10 (shuffle and rewording, each,
  on the subset); (d) **definition-sensitivity annex (cached data):** the sign of
  (DENIED-lost approve-rate − 0.5) on the 2026-07-06 battery agrees between the official
  `retained()` lost-cell definition and the numeric-retention variant (the fresh-eyes ad-hoc
  definition under which haiku read ~0.31 vs our 0.092) — a fingerprint that flips sign across
  reasonable definitions is not a fingerprint. Campaign-level: P-SEC-1(a–c) must hold for ≥
  2/3 models.
- **P-SEC-2 (conditionality — the anti-bias-shelf kill test):** |ablated-cell approve-rate −
  anchored prior approve-rate| ≥ 0.25 for ≥ 2/3 frontier models. If 0/3 clear it, D1 collapses
  into rows 8/25 and is recorded dead.
- **P-SEC-3 (directional forecast):** section measured on {ops_incident, clinical_enroll,
  ci_release} predicts the sign of incorrect anchored decisions on evidence-lost cells:
  (a) held-out surgical domains {loan_underwrite, vendor_sla, sec_triage}: sign-hit ≥ 0.80 per
  model; (b) cached realdoc lost cells (haiku, gpt): ≥ 0.80; (c) cached 2026-07-06 compression
  lost cells (all 3; cross-artifact-type transfer): ≥ 0.80. Denominator = incorrect anchored
  decisions; abstentions/hedges excluded and reported. **Nulls reported beside every hit rate**
  (base-rate laundering guard): coin (0.5) and the truth-marginal baseline (the hit rate of
  predicting the corpus-majority error side with no model information; ≈0.5 by the two-sided
  balanced design on (a), computed empirically on (b)/(c)). **Cross-model control (what makes
  it a fingerprint, not a task property):** for each frontier model A, hit(A | section_A) −
  hit(A | section_sv1) ≥ 0.30, where section_sv1 is the cached fail-open Student-V section —
  the sign-discriminating comparator, since the frontier panel is uniformly deny-leaning; the
  within-panel pairs are reported descriptively (they discriminate magnitude only).
- **P-SEC-4 (two-route taxonomy), confirmatory for the frontier panel:** gpt and haiku satisfy
  conditionality (≥ 0.25 gap from prior); grok is collapsed-prior (gap ≤ 0.15). The student
  routes — V collapsed-inverted (section ≈ trained always-approve prior), J **domain-shrunk**
  (hedge share ≥ 0.5 with the anchored residue same-signed as V: J-training rerouted mass to
  abstention without flipping the section's sign) — are cited from the cached exploratory
  reanalysis, labeled as such; their confirmatory versions belong to the parity-rerun campaign.

## Campaign reading (frozen)

D1 is **upheld** iff P-SEC-1(a–c) holds for ≥ 2/3 models AND P-SEC-2 passes AND P-SEC-3(a)
holds for ≥ 2/3 models with both nulls cleared and the cross-model control met. P-SEC-3(b)/(c)
modulate scope (does the fingerprint transfer across artifact types), not the verdict.
Failures are recorded per prediction; partial outcomes reported as the split they are.

## Cost

≈ 5,040 API calls ≈ $3–5 (haiku-dominated). $0 GPU. Cached-data reanalyses are free.
