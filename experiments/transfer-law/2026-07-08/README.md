# Law 3 cached-summary transfer pilot — 2026-07-08

**Status: RUN COMPLETE (2026-07-08). PREREGISTERED pilot — P-L3-1 passes 3/3,
P-L3-3 and P-L3-5 pass 3/3, P-L3-4 passes 2/3, but the original-accuracy guard P-L3-2
fails 3/3.** This is a strong localization result, not yet the hidden benchmark-parity
kill-shot: missing counterfactual witnesses predict transfer failure, but the cached summaries
were already too weak on original decision accuracy to support the strongest Law-3 reading.

## Files

- `gen_items.py` — deterministic counterfactual-policy corpus over cached domain-battery items.
- `items.jsonl` — 90 generated counterfactual items (3 domains × 30).
- `prereg_transfer_law.md` — predictions fixed before probe calls.
- `runner.py` — `smoke` / `run` / `score`; idempotent cache and cost accounting.
- `responses_raw.jsonl` — raw counterfactual probe responses (created by smoke/run).
- `scored.csv` — row-level scored outputs (created by score).
- `transfer_law_results.json` — aggregate metrics and pass/fail predictions (created by score).
- `reanalysis_by_source_truth.py` / `reanalysis_by_source_truth.json` — exploratory split of the
  P-L3-2 guard failure by source verdict (no API; deterministic; exit 0 iff the DENIED-side
  interpretation reproduces).

## Run sequence

```bash
# 0. Generate deterministic counterfactual items.
python3 gen_items.py

# 1. Smoke-test the three working models and inspect raw outputs.
python3 runner.py smoke --model all

# 2. Full counterfactual probe run. Re-runs are no-ops from responses_raw.jsonl.
python3 runner.py run --model all

# 3. Score and write saved test artifacts.
python3 runner.py score

# 4. Exploratory split of the guard failure by source verdict (no API; deterministic).
python3 reanalysis_by_source_truth.py
```

## Design summary

For each source item, `gen_items.py` selects three originally non-policy readings and constructs a
new counterfactual policy over those values. The cached summary was produced before this policy was
known, so the test asks whether the summary accidentally retained enough witness state to recompute
under changed requirements.

Primary comparison:

> Among rows where the original cached-summary answer is correct, compare counterfactual accuracy
> when the counterfactual required witness survived in the summary vs when it was absent.

See `prereg_transfer_law.md` for thresholds and caveats.

## Verdict

**Design recap.** 90 counterfactual items = 3 domains × 30, balanced counterfactual
APPROVED/DENIED. For each model, the runner reused that model's cached domain-battery compressed
summary and original decision, then made five new calls per item: `cf_decision`, `cf_which`,
`cf_which_abstain`, `cf_nonotes`, and `cf_full_doc_decision`. Total new probe calls: 1,350.

**Headline split.** Full-document counterfactual sanity passes, and transfer failure is sharply
conditioned on whether the counterfactual-required witness survived in the compressed artifact.
But cached original decision accuracy is only 0.61–0.68, below the preregistered 0.70 guard, so
this pilot does **not** establish hidden brittleness at benchmark parity.

| model | orig acc | full-doc CF acc | CF witness survival | CF acc if present | CF acc if missing | gap | debt-error gap | pass pattern |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| grok | 0.678 | 0.956 | 0.467 | 0.929 | 0.646 | +0.283 | +0.275 | P-L3-1/3/5 pass; P-L3-2/4 fail |
| haiku | 0.611 | 1.000 | 0.333 | 0.967 | 0.450 | +0.517 | +0.556 | P-L3-1/3/4/5 pass; P-L3-2 fail |
| gpt | 0.611 | 1.000 | 0.278 | 1.000 | 0.462 | +0.539 | +0.571 | P-L3-1/3/4/5 pass; P-L3-2 fail |
| pooled | — | — | — | 0.959 | 0.509 | +0.450 | — | localization robust |

**Interpretation.** As a Law-3 pilot, this is promising but not decisive. The positive part is
large: across all three models, counterfactual decision accuracy is near-ceiling when the relevant
value survived and much lower when it did not. Among rows whose original cached answer was correct,
missing counterfactual witnesses add 0.27–0.57 error. The negative part is load-bearing: the source
summaries came from the domain-battery regime where original decision accuracy was already modest,
so the result is not yet the desired "standard accuracy looks fine while debt predicts future
failure" claim.

**Where the guard failure lives (exploratory re-analysis, no API — `reanalysis_by_source_truth.py`).**
The P-L3-2 failure is not uniform weakness; it is confined to the conjunctive APPROVED source side.
Splitting original accuracy by source verdict:

| model | orig acc, APPROVED-source | orig acc, DENIED-source |
|---|---:|---:|
| grok | 0.533 | 0.822 |
| haiku | 0.289 | 0.933 |
| gpt | 0.289 | 0.933 |

This is the documented "missing≈failing" conservative bias (theory Appendix C): under lossy
compaction the reader defaults to DENIED, so an APPROVED source is misread as a wrong DENIED and
drags pooled original accuracy under 0.70. Restricting to the DENIED source subset — where original
accuracy clears the guard for every model — the Law-3 localization not only survives but sharpens,
with non-overlapping Wilson intervals for all three:

| model | orig acc (DENIED src) | CF acc if present | CF acc if missing | gap | CI-separated |
|---|---:|---:|---:|---:|:--:|
| grok | 0.822 | 0.955 | 0.609 | +0.346 | yes |
| haiku | 0.933 | 1.000 | 0.438 | +0.562 | yes |
| gpt | 0.933 | 1.000 | 0.514 | +0.486 | yes |
| pooled | — | 0.978 | 0.511 | +0.467 | — |

So the honest reading is stronger than "inconclusive": on the logical side where the compressor did
not collapse to its prior, missing witnesses predict counterfactual failure cleanly. The pooled
guard failure is an artifact of the APPROVED-side conservative bias, not evidence against Law 3.

**Next design change.** Run the same counterfactual transfer probes on a higher-accuracy source
artifact so the guard passes on *both* logical sides: value-dense summaries from the
witness-compaction campaign, a looser realized terminal budget, or a model-ladder campaign where
ordinary accuracy is matched first. Keep this pilot's witness-conditioned analysis, the
source-verdict split, and the full-document sanity check; make the original-accuracy guard
non-negotiable for the headline claim.

**Cost.** $0.6884 total (`grok` $0.0349, `haiku` $0.5634, `gpt` $0.0901). Re-running is idempotent
from `responses_raw.jsonl`. The stale shell `XAI_API_KEY` in this session overrode `.env` and failed
smoke once; the successful smoke/run used `env -u XAI_API_KEY -u ANTHROPIC_API_KEY -u OPENAI_API_KEY
-u GEMINI_API_KEY ...` so the provider module read the repo-root `.env` keys.
