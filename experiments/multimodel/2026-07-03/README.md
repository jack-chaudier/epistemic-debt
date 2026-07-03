# Multi-model campaign — 2026-07-03

Three preregistered phases on one fresh shared corpus (60 items, seed 5151; 30 APPROVED / 30 DENIED with exactly one failing policy parameter; contract-blind compression; temperature 0; idempotent response caches; all prereg files written before the first call of their phase). Models: `grok-4-1-fast-non-reasoning`, `claude-haiku-4-5-20251001`, `gpt-4.1-mini`, and (intended) a Gemini arm.

**Gemini: free-tier (20 req/day/model).** A 360-call same-model arm cannot run (documented in [v5/prereg.md](v5/prereg.md) amendments 1–2), so the Google family was tested two ways: (i) excluded from the v5/transfer/manifest confirmatory cells; (ii) a **micro-arm** ([gemini-micro/](gemini-micro/)) that fits the quota by spreading one probe channel per model bucket over a fixed 20-item stratified sample. Two of its three channels completed and **both preregistered predictions passed** — see Phase 4. All Gemini spend: $0.00.

## Phase 1 — [v5/](v5/): multi-model replication + calibrated-prior criterion

Per-model verdicts (applicability guard: n_lost ≥ 8 and n_retained ≥ 8):

| prediction | grok | haiku | gpt-4.1-mini |
|---|---|---|---|
| P-A5 dissociation (verdict survives, WHICH collapses) | **PASS** | **PASS** | n/a (retention 0.10, retained cell n=2) |
| P-B channel asymmetry (conjunctive side has no shelf) | **PASS** | **PASS** | n/a |
| P-C confabulation locus (ID honest, action fabricates) | **PASS** | **PASS** | n/a |
| P-D abstention as debt detector | **PASS** | **PASS** | n/a |
| P-E calibrated prior (verdict carries gist beyond prior) | **PASS** (0.624 vs 0.500) | **FAIL** (0.574 vs 0.487, Δ=0.087 < 0.10) | n/a |
| P-F incoherence signature | **PASS** (16/22 vs 0/8) | **FAIL** (1/19 — see below) | n/a |

Headline grok cells: decision-lost 19/22, WHICH-lost **0/22**, WHICH-retained 8/8, abstain 18/22 vs 0/8. Haiku: decision-lost 18/19, WHICH-lost **0/19**, WHICH-retained 11/11, abstain 18/19 vs 1/11, but incoherence 1/19 — haiku declines to name a parameter rather than asserting "DENIED + no failing parameter". The incoherence signature is **model-specific**, not universal; the dissociation itself (P-A5–P-D) replicated in 2/2 applicable models. P-E split 1/2: the surviving verdict carries *marginal* gist at best; on haiku it is statistically indistinguishable from prior — the bias-shelf reading survives.

gpt-4.1-mini is a **gist compressor** (drops nearly all numerals at 15 words; retention 0.100). Exploratory 30-word arm ([v5/explore_wide30.py](v5/explore_wide30.py), labeled, not preregistered): cells 20/10, decision-lost 0.75, WHICH-lost 0.15 vs WHICH-retained 1.00, abstain 0.60/0.00, repair fabrication 20/20 — the full pattern reappears at the wider budget.

## Phase 2 — [transfer/](transfer/): does debt travel with the artifact?

4×4 compressor×answerer grid (gemini excluded per above → 3×3 run; 4 applicable off-diagonal pairs under the guard). Preregistered:

- **P-T1 (debt transfers): HOLDS 4/4.** WHICH-lost ≤ 0.107 in *all nine* grid cells; WHICH-retained ≥ 0.909 in all nine. Witness destruction in the artifact is destruction for every reader.
- **P-T2 (verdict shelf transfers): FAILS its threshold 3/4** — grok→haiku decision-lost 0.591 vs the preregistered 0.6 (13/22, one item short). All other cells 0.82–1.00. Reported as a miss; the direction is uniform.
- **P-T3 (no reader recovers witnesses): HOLDS 2/2** applicable compressors.

Exploratory but the sharpest finding of the campaign: **debt quantity is a property of the artifact; debt phenotype is a property of the reader.** On identical summaries, incoherence-on-lost is ~0.73–0.86 when grok or gpt answers and ~0.00–0.05 when haiku answers; haiku's confabulated-WHICH is 0.000 for every compressor. Law 2's phenotype-conversion claim, observed across model families.

## Phase 3 — [manifest/](manifest/): loss-manifest compaction (context-engineering intervention)

Equal-instructed-budget arms: plain-25-words vs 15-word notes + one `OMITTED:` line (≤10 words), both contract-blind. Preregistered per model:

| prediction | grok | haiku | gpt |
|---|---|---|---|
| P-M1 fabrication drops ≥ 30 pts | **FAIL** (1.00→1.00) | **PASS** (0.94→0.54) | **FAIL** (1.00→1.00) |
| P-M2 verdict unharmed (≤ 10 pts) | **FAIL** (0.83→0.60) | **PASS** (0.73→0.73) | **PASS** (0.57→0.52) |

Campaign criterion (all-but-one): **P-M1 fails, P-M2 passes.** The one-line loss ledger raises abstention uptake everywhere (grok 0.60→0.78, haiku 0.63→0.92, gpt 0.61→1.00) but only converts *action-channel* fabrication on the model that is already identification-honest (haiku). Confound note: models overshoot instructed budgets asymmetrically (grok plain25 realized 33.6 words vs manifest 24.5), which contaminates grok's P-M2 fail.

## Phase 4 — [gemini-micro/](gemini-micro/): fourth-vendor confirmation under a free-tier cap

Stratified reader test (12 lost + 8 retained grok summaries), one probe channel per Gemini model bucket to fit 20 req/day/model. Two channels completed in gemini-3.1-flash-lite before Gemini spend was paused: **P-G1 PASS** (which-lost 3/12=0.25, which-retained 8/8) and **P-G2 PASS** (abstain-lost 11/12, abstain-retained 0/8). The artifact-borne-debt result holds on a fourth vendor family. P-G3 (decision channel) unrun. $0.00.

## Phase 5 — [reasoning-reader/](reasoning-reader/): can inference-time compute buy back debt?

gpt-5-mini (reasoning tier) answers from grok's witness-destroyed summaries. **All three preregistered predictions PASS**: which-lost 4/22 (0.18, below guessing), which-retained 8/8, abstain 20/22 vs 0/8, decision-lost 0.909. **Inference-time compute is not a substitute for witness bits** — a smarter reader cannot repair a cheap compactor. Closes the "maybe reasoning recovers it" loophole in the transfer result. $0.19.

## Phase 6 — [coarseness/](coarseness/): does the reason gap track quotient coarseness?

grok, single-condition (p=1) vs six-condition (p=6) policies. **P-S2 PASS** (p=6 witness loss → reason-naming 0/16, guessing) but **P-S1/P-S3 FAIL — informatively**: at p=1 the failing parameter is logically deducible from "DENIED + one condition", yet the model names it on only 2/13 lost items and abstains on 10/13, because (a) the p=1 verdict is a pure always-DENY prior (APPROVED accuracy 0/6) and (b) the model treats reason-naming as *retrieval of the value*, not *inference from structure*. The idealized identity `M_k = Q_(k,1)` does **not** transfer to LLM behavior — the empirical dissociation is *stronger* than the fibration predicts. Recorded as a REFUTED clean prediction with a sharper replacement (theory Appendix G). $0.03.

## Cost

4,805 calls, **$2.04 total** (haiku $1.41, gpt-4.1-mini $0.28, gpt-5-mini $0.19, grok $0.15, gemini $0.00). Every phase has a preregistration written before its first call, raw responses, scored CSVs, and a machine-readable `*_results.json` with preregistered pass/fail. All four provided API keys produced results.
