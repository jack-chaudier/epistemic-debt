# The Justification Budget Line (J = S) — preregistered generalization test

Run 2026-07-06 (design/corpus fixed 2026-07-03; see `prereg_budgetline.md`). 4 confirmatory
arms plus the cached grok/incident Phase-B curve as reference (scored for context, not counted
toward the campaign criterion): budgets
{5,10,15,25,40,60,80} words × 30 DENIED items × {compress, decision, which}. Cost $1.09
(haiku $0.71, gpt $0.31, grok $0.07). Artifacts: `responses_raw.jsonl`, `scored.csv`,
`budgetline_results.json` (prereg parser), `dualparser_results.json` (parser-robustness).

## Candidate law (from H.1, grok-only)

**J = S(artifact):** justified accuracy (WHICH names the true failing parameter) equals
string-checkable witness survival, reader efficiency 1 — slope ≈ 1, intercept ≈ 0 at every
budget. Predictions: **P-L1** |J−S| ≤ 0.10 at all 7 budgets; **P-L2** OLS slope ∈ [0.85,1.15],
|intercept| ≤ 0.08, R² ≥ 0.90. Survives iff both hold on ≥3 of 4 arms incl. ≥1 clinical.

## Verdict: REFUTED as a universal law (1/4 arms; robust to parser choice)

| arm | gap | slope | intercept | R² | P-L1 | P-L2 | law |
|---|---|---|---|---|---|---|---|
| grok/clinical | 0.100 | 0.952 | 0.056 | 0.995 | ✓ | ✓ | **✓** |
| gpt/clinical | 0.100 | 0.917 | 0.088 | 0.999 | ✓ | ✗ (intercept) | ✗ |
| gpt/incident | 0.200 | 0.915 | 0.110 | 0.983 | ✗ | ✗ | ✗ |
| haiku/incident | 0.200 | 0.733 | 0.029 | 0.990 | ✗ | ✗ | ✗ |

Campaign criterion not met under the prereg parser **or** the corrected parser (both give 1/4).
Pooled OLS across the 4 confirmatory arms (n=28 points): **J = 0.923·S + 0.055, R² 0.963.**
Fragility note on the lone pass: grok/clinical's max pointwise gap is exactly 0.100 (3/30 items
at the 15-word budget) — P-L1 passes at the boundary; a single item flip would fail it (P-L2 is
comfortable). The three failing arms miss by wide margins (gaps 0.20 = 6/30 ≫ binomial SE ≈ 0.08),
so the refutation is robust; the confirmation is knife-edge.

## What the refutation says (it is sharper than the law it replaces)

1. **The relationship is affine and tight, but not the identity.** R² is 0.98–0.999 on every
   arm — J is a clean linear function of S everywhere — but slope and intercept are
   **model-dependent**, not universally (1, 0). The pure "reader is a pass-through" result (H.1)
   is **grok-specific**; grok reproduces it on a fresh clinical domain (slope 0.952, R² 0.995).

2. **The direction of the failure is uniform: J ≥ S.** gpt (both domains, intercept 0.088–0.110)
   and haiku (corrected parser, slope 1.203) name the correct failing parameter **more often than
   its value survives the string check**. Across all 7 budgets, gpt/incident has 18 items with
   WHICH correct while the failing value is absent; in 15/18 the failing parameter's *name* has
   zero word overlap with the summary either. Mechanism: the WHICH probe prepends `policy_text`,
   which discloses all three policy parameters by name, so a reader can recover the failing one
   by **elimination over surviving policy values + guessing over the disclosed 3-candidate set**
   (of the 18: 2 admit full elimination — both other policy values survive; 8 partial — one
   survives; 8 pure guess-from-candidates). **Witness string-survival S is therefore a lower
   bound on justified accuracy, not an equality**; the gap J−S is the reader's candidate-set
   recovery, which grok declines to use and gpt/haiku exploit.

3. **The parser artifact corrupts the law verdict, in both directions.** Under the preregistered
   `parse_which` (first-match, optional colon; the bug found in the 2026-07-06 re-score) haiku
   reads as **J < S** (slope 0.733) — verbose correct answers dropped as UNMATCHED. Under the
   corrected last-match parser it flips to **J > S** (slope 1.203). Haiku fails the efficiency
   band either way, but only the corrected parser shows the true (J ≥ S) direction shared with
   gpt. This is a second, independent demonstration (beyond the phenotype re-score) that the
   scoring regex materially changes a scientific verdict — hence both are reported here.

## Audit notes (scoring discrepancies, disclosed)

- **Runner vs prereg arm count (found in audit; fixed 2026-07-06).** `prereg_budgetline.md`
  fixes the campaign criterion over **4 confirmatory arms** (grok/incident cached curve =
  reference, "not re-run", not an arm), but the runner's original `ARMS` list contained 5 entries
  including grok/incident: the reference was double-counted as confirmatory ("1/5"), its rows were
  duplicated in `scored.csv` (420 instead of 210), and the pooled regression included reference
  points (n=35, slope 0.9161). Fixed post-hoc in `runner_budgetline.py` (ARMS→4 + separate
  `REFERENCE`; change commented at the definition) and artifacts regenerated from the idempotent
  cache — zero new API calls. Prereg-conformant numbers: campaign 1/4, pooled n=28 slope 0.9229.
  **The verdict is identical under both counts** (law fails either way; grok/incident fails its
  own P-L1 too). `rescore_dualparser.py` always scored the 4-arm criterion.
- **`clinical_match.resolve_which` was imported but unwired** in the runner's `score()` (the
  dual-parser scorer did call it). Wired in with the same post-hoc fix; **zero numerical effect**
  verified — clinical-arm numbers are bit-identical with and without (models answered with full
  parameter names).
- **Parser dependence** is reported in full in `dualparser_results.json` (see finding 3 above);
  the prereg fixed the v1 parser before the run, so `budgetline_results.json` is the prereg
  verdict and the dual-parser file is the robustness check.

## Consequence for the program

H.1's "reader efficiency ≈ 1, artifact carries the whole exchange rate" holds for grok and does
**not** generalize: readers that exploit disclosed policy structure sit **above** the artifact's
literal witness content. For deployment this cuts against the clean "grep the artifact = measure
justified accuracy" story — a string-survival ledger **under-counts** justified accuracy by the
reader's elimination power, so it is a conservative (safe) lower bound on J but not an estimate of
it. To measure pure witness survival, the probe must not disclose the candidate set; to measure
*deployed* justified accuracy, disclosure is realistic and J ≥ S is the honest model. The revised
claim to carry forward (OBSERVED, 4 arms, corrected parser — the 0.733 haiku slope under the
prereg parser is a measurement artifact, not an efficiency): **J = α·S + β with α∈[0.92,1.20],
β≥0, per-arm R²≥0.96; α=1,β=0 is a grok-specific special case, not a law.** (Range audit-corrected
2026-07-16: corrected-parser arm slopes are {1.203, 0.915, 0.952, 0.917}; the earlier 0.89 lower
bound matched no computable slope.)
