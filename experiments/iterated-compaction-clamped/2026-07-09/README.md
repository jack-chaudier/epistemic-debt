# Iterated compaction, length-clamped — settlement cost vs compound interest (2026-07-09)

Preregistered successor to `experiments/iterated-compaction/2026-07-08` (ρ̄ ≈ 0.93 with the
disclosed length-settling confound). The $0 cache re-analysis of that run showed witness death is
**contraction-gated** (1/346 deaths without length contraction; h0 MLE = 0 on grok/haiku; 0/849
resurrections; exact string fixed points on 26–28/40 items) — see the "settlement cost" row in
`results/RESULTS.md`. This campaign discriminates two opposed frozen predictors:

- **Structural** (hazard h = h0 + σ·max(0, 1 − L_{r+1}/L_r), pooled (0.002, 0.48)): under a
  length clamp, per-round survival ≥ 0.98, net S8/S2 decay ≤ 0.07 — ρ̄ was a settling transient,
  debt is a one-time settlement cost.
- **Fitted-geometric** (ρ̄ is a model constant): S8/S2 = ρ̄^6 ≈ 0.65 (grok) / 0.68 (haiku) /
  0.91 (gpt) — debt compounds every round.

Design (`prereg_clamped.md`, FROZEN 2026-07-09 before any API call): **Arm A** clamp to [36,44]
words with reject-and-retry (≤3 attempts, retries cache-keyed per attempt), R = 8, all 3 models;
**Arm B** single-shot compression of the original doc to {25,30,40} words (state-function
control); **Arm C** grok schedule drop (W=40 rounds 1–4, W=25 rounds 5–8). Same 40-item DENIED
corpus, `retained`/`ANS_RE` scoring, decision probe each round, temperature 0, hard cap 6000
calls, cost cap $3.

Predictions P-RC-0..5 with exact thresholds in the prereg; `runner.py score` emits
`clamped_results.json` with each marked pass/fail plus the predicted-vs-measured table for both
predictors.

Pre-smoke amendments A1–A9 (2026-07-09, dated in the prereg, applied before any API call) close
adversarial-review gaps: headline verdict rule under P-RC-0 inapplicability (A1); in-band
contraction reporting + per-item structural predictor + closer-predictor adjudication when
δ̄ > 0.03 (A2); complete-chain-only scoring (A3); last-match `ANSWER:` parse with multi-match
anomaly counts (A4); per-round in-band rates (A5); power/clustering disclosure (A6); runtime
cost-cap enforcement (A7); corrected smoke arithmetic (A8); P-RC-2 overshoot reading (A9).

## Verdict (run 2026-07-09; 3,887 calls, $1.32, zero parse anomalies)

**Substance: the settlement model is upheld — iteration without contraction does not decay
witnesses.** Formal prereg bookkeeping, exactly as frozen:

- **P-RC-0 guard FAILS 3/3** (in-band 0.872 / 0.847 / 0.650 vs ≥ 0.90): all three models
  overshoot *above* the [36,44] band even through 3 retries, so per amendment A1 the headline
  verdict is **inapplicable as frozen** and everything below is reported per-model. The failure
  direction is over-length — i.e. *even less* contraction (realized δ̄ per item 0.006–0.008),
  which is the regime the hypothesis needs; the guard was mis-frozen as a band when the
  hypothesis only needs a floor. A successor should freeze `L_{r+1} ≥ 0.9·L_r` instead.
- **P-RC-1 band criterion passes 3/3 per-model, both sub-checks 3/3**: with length held, net
  decay over rounds 2–8 is **0.000 (grok) / 0.015 (haiku) / 0.000 (gpt)**
  (S8/S2 = 1.000 / 0.985 / 1.000). Fitted-geometric predicted decay 0.349 / 0.323 / 0.087 —
  wrong by 20–35σ-equivalents of daylight; the structural point predictions (0.963–0.988) are
  slightly *conservative* (frozen h0 = 0.002; reality h0 ≈ 0). Survival curves are literally
  flat: grok [0.983, 0.967×7], gpt [0.658×8], haiku [0.567×5, 0.558×3].
- **P-RC-2 fails-as-frozen (`neither_overshoot`)**: Arm C's forced 40→25 drop kills witnesses
  on cue (S 0.80 → 0.558 in the drop round, then flat 0.542 to R=8) but the drop-round hazard
  0.302 overshoots both the frozen interval [0.10, 0.28] and the structural point at realized
  δ (0.158). Constant-ρ predicted 0.069 — off by 4.4×. Reading: death concentrates at the
  squeeze *more* sharply than the linear hazard fit — the dense-floor second regime (hazard
  given contraction rises once prose padding is exhausted), disclosed in the source
  re-analysis. The structural model is wrong in magnitude at deep squeezes, right in kind;
  the constant-rate model is wrong in kind.
- **P-RC-3 (state function) PASSES**: iterated survival at realized length L matches
  single-shot direct compression to L within 0.008 (round 2) / 0.042 (round 4) — path
  independence, dynamical H.3.
- **P-RC-4 (absorbing) PASSES**: zero resurrections, all four chains.
- **P-RC-5 (verdict persistence) PASSES 4/4**: decision accuracy flat (g1→g8: 0.975→0.95,
  0.875→0.875, 0.95→0.95, 0.925→0.85) — including across Arm C's squeeze, where the verdict
  rides through a 32-point witness drop.
- Free replication: Arm C rounds 1–4 re-run the 2026-07-08 unclamped protocol on grok —
  S4 = 0.80 vs original 0.767.

**One sentence: witness loss is an event, not a rate — debt is charged at budget squeezes
(and then some), is path-independent and absorbing, and is zero at held length, while the
verdict channel is invariant throughout.** The "epistemic interest rate" (row 29) is
re-identified: ρ̄ ≈ 0.93 was the length-settling transient; there is no per-round tax.
Deployable rule: never re-summarize below the settled length; all loss lives in the squeeze.

Caveats: headline formally inapplicable via P-RC-0 (reported above, direction harmless but
rules are rules); P-RC-2 magnitude miss means the two-parameter hazard under-prices deep
squeezes (successor: two-regime hazard with a prose-exhaustion term); haiku Arm-A S1 = 0.567
is lower than the unclamped run's round-1 (clamp retries change round 1 too — within-arm
flatness is the claim, cross-run S1 levels are not); n = 40 items, death clustering caveat
per prereg A6.

## Files

`prereg_clamped.md`, `runner.py`; after the run: `responses_raw.jsonl`, `clamped_results.json`.
Corpus reused from `experiments/domains/2026-07-06/items.jsonl`.
