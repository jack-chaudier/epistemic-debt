# Tier 1 — high-power replication of the within-item dissociation

**Status: RUN COMPLETE (2026-07-06). PREREGISTERED — P-H1/P-H2/P-H4 pass 3/3 models;
P-H3 passes 2/3 (haiku fails on the retained-cell arm).** See Verdict below.

Kills the statistical-n fear: same protocol as v4/v5, one domain (ops_incident), one 15-word
budget, **N=400 (200 DENIED)** → lost/retained cells near 120/80, Wilson CIs ≈ ±0.05 vs the
±0.15 of the original n=14–22 cells. Predictions fixed in `prereg_highpower.md` (P-H1…H5).

## Files

- `items.jsonl` — 400 items, seed 706010, selfcheck clean (0 confound problems).
- `gen_items.py` — regenerates the corpus (deterministic; no LLM).
- `runner.py` — `run` / `smoke` / `score` over the shared `lib/dissociation.py` protocol.
- `../../lib/domains.py`, `../../lib/dissociation.py` — shared corpus + protocol libraries.

## Run sequence (the ground-rule gate first)

```bash
# 0. smoke — 3 items end-to-end, INSPECT the raw outputs before spending (~$0.02)
python3 runner.py smoke --model grok

# 1. primary run — variant 0, all three models (idempotent; resumes on rerun)
python3 runner.py run --model grok
python3 runner.py run --model haiku
python3 runner.py run --model gpt

# 2. probe-robustness arm — grok under paraphrased probes (labeled, secondary)
python3 runner.py run --model grok --variant 1

# 3. score — writes highpower_results.json with predictions marked pass/fail
python3 runner.py score
```

Reader = compressor; hard cap 8,000 calls/model; est. < $4 total. Re-running a completed arm
is a no-op (idempotent cache in `responses_raw.jsonl`).

## Verdict

**Design recap.** N=400 items (200 DENIED), ops_incident, reader = compressor, contract-blind
15-word compaction, v5 protocol (compress → decision, which, which_abstain, repair, nonotes),
corrected last-anchor parser. Three models at variant 0 plus a grok paraphrase arm (variant 1).
All cells below are variant 0; CIs are Wilson 95%.

**The dissociation survives high power.** With lost/retained cells of n=125–149 / 51–75
(CIs ±0.03–0.09 vs the ±0.15 of the original n=14–22 cells), P-H1 passes for all three models
with no CI anywhere near overlap:

| model | retention | which_lost (CI) | which_retained (CI) | P-H1 |
|---|---|---|---|---|
| grok  | 0.300 (140/60) | 0.007 (0.001, 0.039) | 0.900 (0.799, 0.953) | **pass** |
| haiku | 0.255 (149/51) | 0.054 (0.028, 0.102) | 0.980 (0.897, 0.997) | **pass** |
| gpt   | 0.375 (125/75) | 0.128 (0.080, 0.198) | 0.960 (0.889, 0.986) | **pass** |

**Per-prediction outcomes (variant 0):**

- **P-H1 (dissociation)** — **pass 3/3**. Every `which_lost` upper CI < 0.20; every
  `which_retained` lower CI > 0.79; all `which_lost.p` < 0.34.
- **P-H2 (verdict survives)** — **pass 3/3**. `decision_lost` = 0.807 (grok), 0.899 (haiku),
  0.992 (gpt), all ≥ 0.75.
- **P-H3 (abstention detects debt)** — **pass 2/3, haiku FAILS**. Lost-cell abstention: grok
  0.657, haiku 1.000, gpt 0.848 (all ≥ 0.60). Retained-cell abstention: grok 0.017, gpt 0.000
  (≤ 0.15) but haiku 0.176 (9/51, CI 0.095–0.303) > 0.15 — haiku over-abstains even when the
  witness survives, consistent with its calibration-first phenotype from the re-score campaign.
  Reported as a fail per prereg; the failure direction is excess caution, not confabulation.
- **P-H4 (confabulation locus)** — **pass 3/3**. `repair_specific_lost` = 1.00 (grok), 0.664
  (haiku), 1.00 (gpt), all ≥ 0.60; `which_confab_lost` = 0.064, 0.027, 0.120, all ≤ 0.25.
  The action channel fabricates a concrete change while the identification channel declines.
- **P-H5 (prior guard, characterization)** — `nonotes_deny_rate` / `approved_denied_under_loss`:
  grok 1.00/1.00 (pure always-DENY prior — its surviving verdict is the bias shelf, not
  evidence-reading), haiku 0.585/0.580, gpt 0.535/0.515 (near-chance priors — their surviving
  verdicts are *not* explained by an always-DENY prior; gpt's decision_lost = 0.992 with a
  0.535 prior is the strongest verdict-survival datum in the program so far).

**Paraphrase arm (grok variant 1) — inapplicable under the prereg guard, direction consistent.**
The paraphrased compression instruction ("reduce to 15 words or fewer") halved grok's realized
summary length (mean 9.1 words vs 18.1 at variant 0), collapsing fail-retention to 0.01
(198 lost / 2 kept). Per the applicability guard (retention ≤ 0.15) P-H1/H4 are not scoreable —
the runner JSON's mechanical `true` for variant-1 P-H1 rests on an n=2 retained cell and should
be read as inapplicable. Within the populated lost cell the pattern is unchanged: which_lost =
0.000 (CI 0–0.019), decision_lost = 0.753, abstain_lost = 0.894, repair_specific = 1.00. So the
dissociation is not an artifact of one probe wording, but the planned CI comparison could not be
run; realized (not instructed) compression length is confirmed as the operative variable.

**Watch-items / audit notes.**

- **repair_param_correct_lost** sits at the 1/3 candidate-disclosure floor for grok (0.343) and
  haiku (0.309); gpt is above it (0.424, CI 0.341–0.512). Investigated before writing this
  verdict: conditioning on how many *sibling* candidate witnesses survive in the summary,
  P(repair hits the true parameter | 0 siblings retained) = 0.385 (37/96, CI incl. 1/3) for gpt,
  0.349 grok, 0.193 haiku, rising monotonically to 1.0 at 2 siblings retained (gpt 3/3, haiku
  8/8). The excess is elimination over the disclosed candidate set using partially surviving
  sibling readings — the budgetline candidate-disclosure mechanism (confound #3), not a scoring
  leak. Only 3/53 gpt repair hits had the failing parameter named in the summary.
- **Anomaly counts** (never silently binned): grok and gpt have 0 UNMATCHED / 0 unparsed calls.
  haiku: 5 UNMATCHED `which`. Four (lost cell) are a **parser edge case, disclosed not fixed**:
  the anchor regex matches the *prose* word "parameter:" (e.g. "…naming a single parameter:")
  case-insensitively, `\s*` crosses the following blank line, and the capture swallows the true
  final "PARAMETER: NONE" line, yielding raw "PARAMETER: NONE" → UNMATCHED instead of NONE.
  Semantically all four are NONE; `which_correct`/`which_confab` are unaffected (both false
  either way), only the NONE-subsplit denominators shift, so no prediction is touched and the
  preregistered parser was left unmodified. The fifth (retained cell) answers "battery reserve"
  for `reserve charge margin` — a fuzzy-match miss, semantically correct, so `which_retained`
  is undercounted by one (0.980 reported vs 1.000 semantic; conservative for P-H1),
  42 unparsed `which` and 26 unparsed `decision` (verbose "I cannot determine…" refusals with no
  anchor — semantically abstentions, 25/42 on APPROVED items, 17/42 in the lost cell where they
  count against which_lost, i.e. *conservative* for P-H1). Hand-inspected 10 lost-cell raws per
  model: parses match semantics.
- **NONE-split heuristic**: `none_missing_lost` = 0.97 for haiku (says "missing data" when
  saying NONE) vs 0.00–0.01 for grok/gpt (bare NONE) — the string heuristic; semantic-judge
  split deferred as preregistered.
- **Realized compression length** (instructed budget 15 words): gpt mean 24.2 (median 15),
  haiku 23.4 (19), grok 18.1 (12), grok-v1 9.1 (9). gpt/haiku overshoot the instruction;
  retention differences track realized length.
- **gpt applicability**: unlike the multimodel campaign (retention ≤ 0.15 → inapplicable), gpt
  retains 0.375 here on this corpus/generator, so it is applicable and passes everything —
  the strongest cross-model cell in the table.

**Cost.** grok $0.34 (both variants), haiku $2.58, gpt $0.35 — **$3.26 total** (9,600 calls
incl. smoke; response cache made all crash-resumes free).

**Interpretation.** The statistical-n fear is dead: at CIs of ±0.03–0.09 the within-item
dissociation is not a small-sample artifact. What got stronger: verdict-survival is now
demonstrated in two models (haiku, gpt) whose no-notes prior is near chance, so "the answer
survives compaction" is no longer attributable to an always-DENY prior for the panel as a
whole — grok remains a pure prior-rider and is interpreted per the bias-shelf reading. What
got weaker: P-H3's clean abstention story — haiku over-abstains in the retained cell, so
abstention as a debt *detector* has a model-specific false-positive rate; and the paraphrase
arm shows probe wording can move realized compression enough to empty the retained cell,
making "15 words" a nominal, not effective, budget knob.
