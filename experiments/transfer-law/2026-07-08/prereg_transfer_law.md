# Law 3 cached-summary transfer pilot — preregistration

Fixed 2026-07-08, before any counterfactual probe calls. This is a **pilot**, not the full
teacher/student ladder: it reuses the 2026-07-06 domain-battery cached summaries for the three
working `.env`-backed models (`grok`, `haiku`, `gpt`) and adds counterfactual policy probes.
No new compression calls are made.

## Purpose

Test the first empirical form of Law 3: **epistemic debt predicts brittleness under intervention**.
The prior campaigns show that contract-blind compression can preserve ordinary answers while
losing the witness. This campaign asks whether the same compressed artifacts fail when the
policy changes and the reader must recompute from retained values.

## Corpus

`gen_items.py` selects 90 cached domain-battery source documents:

- 3 domains: `ops_incident`, `clinical_enroll`, `ci_release`.
- 30 source items per domain, balanced over original APPROVED/DENIED.
- Each counterfactual policy uses 3 originally non-policy readings from the same document.
- Counterfactual truth is balanced within each domain: 15 APPROVED, 15 DENIED; DENIED has exactly
  one failing counterfactual parameter.
- Mechanical selfcheck enforces: 3 counterfactual parameters, exactly one failure when DENIED,
  unique string-retention target for every counterfactual value, and threshold/truth consistency.

The source document is unchanged; only the policy changes. The compactor was blind to this future
policy when it produced the cached summary.

## Models

Use the three existing working aliases from `experiments/multimodel/2026-07-03/providers.py`:

| alias | provider family | role |
|---|---|---|
| `grok` | xAI | cached compressor and counterfactual reader |
| `haiku` | Anthropic | cached compressor and counterfactual reader |
| `gpt` | OpenAI | cached compressor and counterfactual reader |

Keys come from environment or repo-root `.env` via the existing provider module. Key material is
never written to artifacts.

## Probes

For each model/item, the runner reuses that model's cached source summary and asks:

1. `cf_decision`: decision under the counterfactual policy from compressed notes.
2. `cf_which`: reason under the counterfactual policy from compressed notes.
3. `cf_which_abstain`: same as `cf_which`, with explicit `INSUFFICIENT_EVIDENCE` option.
4. `cf_nonotes`: policy-only prior baseline.
5. `cf_full_doc_decision`: sanity check on the full original document under the counterfactual policy.

Scoring uses the corrected last-anchor `PARAMETER:` parser from `experiments/lib/dissociation.py`.
All rows are written to `scored.csv`; aggregate predictions are written to
`transfer_law_results.json`.

## Definitions

- **Original accuracy guard**: source-domain cached `decision` answer equals the original truth.
- **Counterfactual required witness survived**:
  - if counterfactual truth is DENIED: the failing counterfactual value appears in the summary;
  - if counterfactual truth is APPROVED: all three counterfactual policy values appear.
- **Counterfactual transfer accuracy**: `cf_decision` equals counterfactual truth.
- **Debt-localized transfer failure**: among original-correct rows, counterfactual error is higher
  when the counterfactual required witness is absent than when it survives.

String survival is treated as a conservative artifact-side lower bound, not as a full estimator of
justified accuracy (per the budget-line refutation).

## Preregistered predictions

Per model:

- **P-L3-1 full-doc sanity:** `cf_full_doc_accuracy >= 0.90`.
- **P-L3-2 original-accuracy guard:** cached-summary original decision accuracy `>= 0.70`.
- **P-L3-3 witness-conditioned transfer:** `cf_decision_accuracy(required present) -
  cf_decision_accuracy(required missing) >= 0.20`.
- **P-L3-4 reason channel:** on counterfactual-DENIED items, `cf_which_missing < 0.34` and
  `cf_which_retained >= 0.75`.
- **P-L3-5 debt localizes failure:** among original-correct rows, counterfactual error is at least
  0.20 higher when the counterfactual required witness is missing than when it survives.

Campaign reading: the Law-3 pilot is promising if P-L3-1/2 pass and P-L3-3 or P-L3-5 passes on at
least two of the three models. P-L3-4 is the reason-channel replication under a changed policy.

## Budget and cap

90 items × 3 models × 5 calls = 1,350 calls, no compression. Hard cap 2,000 new calls/model.
Estimated spend: under $2. Re-running is idempotent via `responses_raw.jsonl`.

## Known risks / watch items

- The counterfactual policy discloses the three candidate parameters; this measures deployed
  recomputation with policy disclosure, not candidate-blind artifact content.
- Some counterfactual witnesses may survive even when original witnesses were lost; the primary
  conditioning is therefore on the counterfactual required witness itself.
- Parser artifacts remain possible for acronyms; `UNMATCHED`/raw outputs are saved in `scored.csv`.
  A semantic-judge re-score is the correct follow-up for phenotype claims.
- Nominal source summaries have different realized lengths by model/domain; `summary_words` is
  recorded per row and interpreted as the operative compression variable.
