# Phase 1 preregistration — the Justification Budget Line (candidate law)

Fixed 2026-07-03, before any Phase 1 API call.

## Candidate law

**J = S(artifact).** Justified accuracy of a compaction pipeline equals the string-checkable
witness survival of its artifact, with reader efficiency 1: slope ≈ 1, intercept ≈ 0, at every
budget. Established so far on ONE model (grok) and ONE domain (incident files): result 17,
`|WHICH − fail-survival| ≤ 0.07` at all 7 budgets. This phase promotes or kills it as a law by
testing on two further models and one genuinely new item domain.

## Definitions

Per (arm, budget b), over the 30 DENIED items of the arm's corpus:

- **S_b** (witness survival) = fraction of items whose failing-parameter value survives in the
  compressed notes, by the tolerant string check `retained()` (runner3, unchanged).
- **J_b** (justified accuracy) = fraction of items where the WHICH probe names the true failing
  parameter (`parse_which()`, unchanged).
- **D_b** (decision accuracy) recorded for the shelf context, not part of the law test.

Reader = compressor (same model both stages) in all confirmatory arms.

## Design

Budgets **{5, 10, 15, 25, 40, 60, 80} words**, plain contract-blind compaction prompt (v5
wording, budget substituted — identical to the Phase B curve prompt). Per (arm, budget, item):
COMPRESS, DECISION, WHICH = 3 calls.

Confirmatory arms (4):

| arm | model | corpus |
|-----|-------|--------|
| haiku/incident | claude-haiku-4-5 | v5 items, 30 DENIED (same corpus as the grok curve) |
| gpt/incident | gpt-4.1-mini | same |
| grok/clinical | grok-4-1-fast-non-reasoning | fresh clinical-enrollment corpus, 30 DENIED |
| gpt/clinical | gpt-4.1-mini | same |

The existing grok/incident curve (Phase B, cached) is the reference arm; it is not re-run.

**New domain — clinical trial enrollment.** Fresh generator (`gen_clinical.py`, seeded):
patient charts (~750 words) with 12 numeric labs/vitals (3 secretly eligibility-relevant),
clinical-register narrative and number-free distractor sentences; policy = conjunction of 3
threshold criteria, APPROVED/DENIED verdict tokens kept so all v3 scoring machinery applies
unchanged. Confound checklist applied as in v2–v5: no salience difference between policy and
non-policy labs (same sentence templates, shuffled order); no verdict language in the document
(thresholds never appear; no eligibility/spec words); all numeric values pairwise distinct and
non-round so `retained()` cannot false-positive (metric confound); parameter names pairwise
word-disjoint enough for `match_param`. Corpus is inspected (3 items smoke-tested end to end)
before the full spend.

## Preregistered predictions

Per confirmatory arm:

- **P-L1 (pointwise budget line)**: `|J_b − S_b| ≤ 0.10` at every one of the 7 budgets.
- **P-L2 (unit line)**: OLS of the 7 (S_b, J_b) points: slope ∈ [0.85, 1.15], |intercept| ≤ 0.08,
  R² ≥ 0.90.

Campaign criterion: **the law survives** iff P-L1 and P-L2 both pass on ≥ 3 of 4 arms,
including at least one clinical arm. Anything less is reported as a refutation or partial
result, and the failing regime is characterized (reader efficiency J_b/S_b per budget, which
side of the line it falls on, whether the break is model- or domain-specific).

Applicability guard (per arm, as in v5): if an arm's S never exceeds 0.5 at any budget (the
compressor collapses to pure gist everywhere), P-L2's slope is unidentifiable on that arm; the
arm is reported as inapplicable for P-L2 (P-L1 still binds) and does not count toward the 3-of-4.

## Exploratory (labeled)

Item-level J×S agreement tables; reader efficiency J/S per budget; logistic midpoints per arm;
pooled cross-arm regression; decision-accuracy curves.

## Budget

4 arms × 7 budgets × 30 items × 3 calls = 2,520 calls; hard cap 2,800. Estimated < $2.5.
