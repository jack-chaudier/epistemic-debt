# Preregistration — Iterated compaction, length-clamped: settlement cost vs compound interest

**FROZEN 2026-07-09, before any API call.** Corpus, scoring (`retained`/`ANS_RE`), models, and
protocol machinery are unchanged from `experiments/iterated-compaction/2026-07-08` (the run this
succeeds). This campaign discriminates two OPPOSED predictors frozen from the $0 cache re-analysis
of that run (849 value-transitions; deaths contraction-gated: 1/346 deaths without length
contraction; per-model MLE h0 = 0 on grok/haiku; 0/849 resurrections; exact normalized-string
fixed points on 26–28/40 items by S3→S4). See the "settlement cost" row in `results/RESULTS.md`
(2026-07-09).

## The two frozen predictors (both stated, numbers fixed now)

**Predictor 1 — structural (contraction-gated hazard).** Per-value per-round death hazard
h = h0 + σ·max(0, 1 − L_{r+1}/L_r), with pooled (h0, σ) = **(0.002, 0.48)** and per-model
σ = **0.64 (grok) / 0.54 (haiku) / 0.18 (gpt)**, all frozen from the 2026-07-08 cache fit.
Under an effective length clamp (δ_r ≈ 0 for rounds 2–8) it predicts: per-round conditional
survival S_{r+1}/S_r ≥ 0.98 every round, **net S8/S2 ≥ 0.87** (point prediction ≈ 0.988 at
δ = 0). The measured ρ̄ ≈ 0.93 was a length-settling transient; compaction debt is a one-time
**settlement cost** set by terminal length, not compound interest.

**Predictor 2 — fitted-geometric (ρ̄ is a model constant).** ρ̄ frozen at the 2026-07-08 measured
values 0.931 / 0.937 / 0.985 (grok/haiku/gpt). Predicts **S8/S2 = ρ̄^6**: grok **0.651**, haiku
**0.677**, gpt **0.913** — decay compounds every round regardless of the length schedule.

Honest power note: gpt discriminates weakly (0.913 vs 0.988; gap 0.075 sits inside the
"revise" band below). The primary discriminators are grok and haiku (gaps ≈ 0.31–0.34,
spanning the preregistered pass/fail bands).

## Design

Corpus: the same 40 DENIED items (balanced ops_incident / clinical_enroll / ci_release,
deterministic first-N selection) from the frozen 2026-07-06 domain battery. Reader = compressor,
contract-blind, same instruction skeleton. Witness survival S = mean `retained(summary, value)`
over the 3 policy values (string check); decision probe (`ANS_RE`) each round as in the original.
Temperature 0; item selection and all logic deterministic (no sampling anywhere); idempotent
cache keyed by (model, item, call).

- **Arm A (clamp — the head-to-head):** grok, haiku, gpt; **R = 8 rounds, W = 40**. Clamped
  instruction demands 36–44 words. **Reject-and-retry**: if a generation's realized length is
  outside **[36, 44] words**, retry with deterministic corrective feedback (previous attempt +
  its word count quoted), **max 3 attempts**; keep the **first in-band attempt**, else the
  **LAST attempt**. Kept-attempt rule is fixed here and implemented identically at run and score
  time. Cache keys the retries distinctly (`a_compress{r}_try{t}`) so a rejected attempt is never
  replayed as the kept artifact. Attempt counts and in-band flags recorded and reported.
- **Arm B (single-shot state-function control):** compress the ORIGINAL document directly to
  targets **{25, 30, 40}** words (unclamped instruction), same corpus, all 3 models. Gives
  S_direct(L) for P-RC-3. Decision probe per target (descriptive).
- **Arm C (schedule drop, grok only for cost):** unclamped W = 40 for rounds 1–4, forced budget
  drop to **W = 25 at round 5**, continue at 25 through R = 8. Rounds 1–4 are an exact protocol
  replication of the 2026-07-08 grok chain on a fresh cache (no response reuse) — an incidental
  replication check, reported under exploratory.

## Preregistered predictions (exact thresholds)

- **P-RC-0 (clamp guard, per model — validity, not pass/fail of the law):** ≥ **90%** of Arm-A
  kept round-artifacts (40 items × 8 rounds) realize length in [36, 44] words. A model failing
  this has Arm A marked **inapplicable** (reported; excluded from P-RC-1 and the headline
  predictor table).
- **P-RC-1 (pure-iteration rate ≈ 0 — the confirmatory head-to-head):** per applicable model,
  net decay D = 1 − S8/S2 in Arm A. **D ≤ 0.07 → structural PASS; D ≥ 0.20 → structural FAIL
  (fitted-geometric band); 0.07 < D < 0.20 → REVISE** (two-source model: some decay survives the
  clamp). The band is the confirmatory criterion. Sub-checks reported (not confirmatory):
  every conditional survival S_{r+1}/S_r ≥ 0.98 for r = 2..7, and S8/S2 ≥ 0.87. Headline =
  all applicable models in the PASS band; a secondary reading on the primary discriminators
  (grok, haiku) is also reported.
- **P-RC-2 (schedule-dependence of ρ — Arm C, grok):** drop-round hazard = per-value conditional
  death rate on the S4→S5 transition (deaths / at-risk; equals 1 − S5/S4 when absorbing).
  Structural predicts h = 0.002 + 0.64·δ5 (δ5 assumed 0.30–0.40 → point ≈ 0.20); frozen pass
  interval **[0.10, 0.28]**. Constant-ρ predicts ≈ **0.069** (1 − 0.931). Outcome: in-interval →
  **PASS**; < 0.10 → **FAIL (constant-ρ favored)**; > 0.28 → neither (overshoot). **Guard G-C:**
  mean realized δ̄5 = mean_item max(0, 1 − L5/L4) must be ≥ **0.15**, else P-RC-2 is
  **inapplicable** (the drop didn't bite; both predictors' realized-δ point predictions still
  reported, no pass/fail).
- **P-RC-3 (state function — H.3 dynamical, grok):** |S_r(Arm C) − Ŝ_direct(L̄_r)| ≤ **0.08** at
  r ∈ {2, 4} (the unclamped rounds), where Ŝ_direct is the piecewise-linear interpolation of
  grok Arm B (mean realized length, mean S) points, clamped at the endpoints. Pass = both rounds
  within 0.08. (Same-corpus by design: the cross-corpus version is known invalid — grok round-1
  S 0.95 @ 43.6w on domains vs 0.844 @ 48w on v3-incident.)
- **P-RC-4 (absorbing death):** resurrection rate (value absent at r, present at r+1) < **1%** of
  value-transitions on every iterated chain (Arm A × 3 models, Arm C). Pass = all chains.
- **P-RC-5 (verdict eigenvalue 1):** decision-probe accuracy g8 ≥ g1 − **0.10** on every iterated
  chain (Arm A × 3 models, Arm C). Arm B has no rounds; its per-target decision accuracy is
  reported descriptively (P-RC-5 does not apply to it).

### Verdict logic (fixed now)

- **Structural model upheld:** P-RC-1 PASS on all applicable models AND P-RC-2 ∈ {PASS,
  inapplicable}.
- **Fitted-geometric upheld (ρ was real physics):** P-RC-1 FAIL (D ≥ 0.20) on both grok and
  haiku AND P-RC-2 ∈ {FAIL, inapplicable}.
- Anything else: **mixed** — reported prediction-by-prediction, no post-hoc relabeling.
  P-RC-3/4/5 qualify the model reading (state-function, absorbing, verdict invariance) and are
  reported pass/fail regardless of the head-to-head outcome.
- Either headline outcome is fully reportable; if Arm A shows ρ_clamp ≈ 0.93 the structural
  model is dead and the constant was real. That is a result, not a failure of the campaign.

## Exploratory (labeled, no confirmatory weight)

- Haiku fixed-point rate rises by R = 8: fraction of exact normalized-string fixed points on the
  2→3 transition vs the 7→8 transition (Arm A haiku); prior run had haiku at only 3/40 by S3→S4.
- Plateau values: Arm C grok S4 within ±0.03 of **0.767** (also the replication check of the
  2026-07-08 run); gpt Arm A S8 within ±0.03 of **0.883** (its natural length ≈ 42 is in-band,
  so clamp ≈ no-op for gpt); haiku Arm A S8 reported against **0.542** but flagged
  non-comparable under the structural reading (the clamp blocks the settling that produced 0.542
  — the two predictors disagree here, which is informative but not preregistered-confirmatory).
- Copy-containment (unigrams of S_r found in S_{r−1}) per round per chain — separates paraphrase
  churn from eviction under the clamp confound below.

## Confounds disclosed (CLAUDE.md checklist)

1. **Clamp instruction changes T (padding pressure):** demanding ≥ 36 words may itself corrupt
   values (forced elaboration/hallucinated padding). Monitored via per-round copy-containment and
   the decision probe; disclosed, not eliminated. If S *rises* implausibly or containment drops
   sharply under clamp, that is reported as a clamp artifact.
2. **Reject-retry selection effect:** retrying selects compliant generations, and the retry
   prompt quotes the model's previous attempt. Attempt counts, per-round in-band rates, and the
   fixed kept-attempt rule (first in-band, else last) are all reported; P-RC-0 bounds how much
   selection occurred.
3. **Parse:** S is the numeric `retained()` string check (parser-insensitive); decision via
   `ANS_RE` with UNMATCHED counts surfaced in the results JSON, never silently binned.
4. **Candidate-set disclosure:** N/A to S (artifact-content measure, hidden candidates); the
   decision probe discloses the policy text as usual — deployed-verdict reading, stated.
5. **Determinism:** temperature 0, idempotent cache keyed (model, item, call) with retries keyed
   by attempt index, deterministic item selection, global hard call cap. Re-running a completed
   experiment is a no-op.

## Budget and cost cap

Exact call counts (40 items):

| arm | per model | models | min | expected | max |
|---|---|---|---|---|---|
| A (8 rounds × [1–3 tries + 1 decision]) | 640–1280 | 3 | 1920 | ≈ 2220 (1.3 tries/round) | 3840 |
| B (3 targets × 2 calls) | 240 | 3 | 720 | 720 | 720 |
| C (8 rounds × 2 calls) | 640 | grok | 640 | 640 | 640 |
| **total** | | | **3280** | **≈ 3580** | **5200** |

**Hard cap 6000 calls total** (enforced in runner, all arms/models pooled). Estimated cost,
calibrated on 2026-07-08 actuals ($0.314 / 960 calls, haiku $0.218 of it): expected ≈ **$0.75–1.0**
(haiku ≈ $0.45–0.60, gpt ≈ $0.17, grok ≈ $0.15), upper bound with maximal retries ≈ **$1.5**.
**Cost cap $3.00.** Smoke test (3 grok items all arms + 1 haiku item Arm A, ≈ 260 calls, ≈ $0.05)
runs first and its raw outputs are read before the full spend; smoke calls are cache-shared with
the full run.

## Deviations from the frozen design note (scratchpad `spectral-rho.md` §3), with justification

1. **Arm C is 640 calls exact** (doc estimated ~770): 40 items × 8 rounds × 2 calls.
2. **Added guard G-C (δ̄5 ≥ 0.15) to P-RC-2.** The doc assumed δ5 ≈ 0.30–0.40, but the prior
   unclamped run shows grok settles to L4 ≈ 28.9 words, so a 25-word budget may realize
   δ5 ≈ 0.15–0.25; without the guard a correct structural model could miss the frozen interval
   merely because the drop didn't bite. The guard is fixed before any call.
3. **P-RC-1's confirmatory criterion is the D-band** (≤ 0.07 / ≥ 0.20). The doc's other two
   statements (per-round ≥ 0.98; S8/S2 ≥ 0.87) are not numerically identical to the band and are
   demoted to reported sub-checks.
4. **P-RC-5 restricted to iterated arms** (A, C); Arm B has no round structure.
5. **Exploratory plateau mapped to measurable chains** (Arm C S4 vs 0.767; gpt Arm A S8 vs 0.883;
   haiku Arm A S8 vs 0.542 flagged non-comparable under the structural reading) — the doc's
   {0.77, 0.54, 0.88} triple presupposed unclamped R = 8 chains that this design does not buy
   for haiku/gpt.
6. **Global hard cap 6000 calls** (orchestrator instruction) replaces the per-model 2000 of the
   predecessor.

## Pre-smoke amendments — 2026-07-09, before any API call (adversarial-review items in parens)

Verified `responses_raw.jsonl` does not exist at amendment time; zero spend so far. These
amendments close gaps found in review of the frozen text above; nothing above is deleted.

- **A1 (review 1) — headline rule under P-RC-0 inapplicability.** Either headline verdict
  requires at least one primary discriminator (grok, haiku) applicable; the fitted-geometric
  verdict requires BOTH applicable (its criterion is "FAIL on both"). If neither grok nor haiku
  passes P-RC-0, the headline is **inapplicable** — per-model report only, no
  structural/fitted/mixed verdict. `primary_discriminators_pass` is null (not vacuously true)
  when no primary discriminator is applicable. This is a live scenario: grok/haiku settle to
  ≈29 words unclamped, well below the [36,44] band.
- **A2 (review 2) — in-band contraction.** The [36,44] band still permits per-round contraction
  up to δ = 1 − 36/44 ≈ 0.18, and a mean-L δ understates per-item δ (oscillation cancels in the
  round mean). Therefore: (i) per-item realized δ_r distributions (transitions 1→2 .. 7→8,
  complete chains) are reported per Arm-A model; (ii) the predictor table carries a **per-item**
  structural prediction — mean over complete-chain items of ∏_{r=3..8}(1 − h0 − σ·δ_item,r) —
  alongside the mean-L version; (iii) adjudication rule, fixed now: let δ̄ = mean per-item δ over
  transitions 2→3 .. 7→8. If δ̄ ≤ **0.03** the D-band above is the P-RC-1 criterion as frozen.
  If δ̄ > 0.03 the clamp did not achieve δ ≈ 0 and that model's headline P-RC-1 outcome is
  instead the **closer-predictor rule**: measured S8/S2 vs per-item structural-at-realized-δ
  (per-model σ) and vs ρ̄^6 — structural closer → PASS, fitted closer → FAIL, exact tie →
  REVISE. The raw band outcome is reported regardless.
- **A3 (review 3) — complete-chain scoring.** All round means, S-curves, transitions, and P-RC
  computations on iterated chains use only items whose chain reached all R rounds; partial
  chains (any missing round) are counted in `anomalies.partial_chains` and excluded, so S8 and
  S2 are always computed on the same item set (no survivor-composition bias after an
  interrupted run).
- **A4 (review 4) — decision parse.** Authoritative decision = the **last** `ANSWER:` match in
  the reply (repo battle scar #2: last-anchor parsing). Multi-match counts and first-vs-last
  disagreement counts are surfaced in `anomalies`. The predecessor scored first-match; any
  cross-run g-curve comparison will note this (P-RC-5 is internal to this run, so it is
  unaffected by the change of convention).
- **A5 (review 5) — per-round in-band rates** are emitted per Arm-A model, not just the overall
  fraction; P-RC-0's denominator is the kept round-artifacts actually executed (full-run target
  40 × 8 per model).
- **A6 (review 6) — power/clustering.** Deaths cluster within items and contraction events, so
  binomial SEs are anti-conservative. P-RC-2 is low-powered: ~90–95 at-risk values, and the
  constant-ρ point 0.069 sits ≈1 binomial SE below the pass boundary 0.10 — a true-constant-ρ
  world lands inside the structural interval perhaps 15–25% of the time, so a P-RC-2 PASS is
  weak evidence on its own. The head-to-head weight rests on P-RC-1, whose grok/haiku gaps
  (≈0.31–0.34) exceed any plausible cluster-adjusted SE. Per-item death clustering
  (deaths-per-item histogram per chain) is reported in the results JSON.
- **A7 (review 7) — cost cap enforcement.** The $3.00 cap is enforced at runtime: the runner
  accumulates realized cost (from cached usage plus each new response) and refuses further
  calls at the cap; the 6000-call hard cap independently bounds the worst case at ≈ $2.
- **A8 (review 8) — smoke arithmetic corrected.** 3 grok items × [A 16–32 + B 6 + C 16] +
  1 haiku item × [A 16–32] = **130–194 calls** (not ≈260), ≈ $0.03.
- **A9 (review 9) — P-RC-2 overshoot corner.** If realized δ̄5 puts the structural point
  h0 + σ_grok·δ̄5 outside the frozen [0.10, 0.28] (δ̄5 > ≈0.43), the frozen-interval outcome is
  still recorded exactly as stated above, and the reported `structural_point_at_realized_delta`
  vs measured-hazard comparison is descriptive only — no post-hoc pass/fail relabeling.
