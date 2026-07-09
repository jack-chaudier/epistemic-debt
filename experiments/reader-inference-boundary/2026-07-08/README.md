# Reader inference boundary — how much does the read channel *compute*? (2026-07-08)

Preregistered: `prereg_reader_inference_boundary.md` (main), `prereg_c2_confirmatory.md` (attempted
leak fix; confirmatory status VOID after audit). New spend **$0.91** (main $0.72 + c2 $0.19),
1,980 calls, 3 models. Candidates DISCLOSED
(deployed-J setting). Reader = the model reading constructed notes; **no compressor** — the notes
are built deterministically so the required read-channel operation is controlled exactly.

## The question

The repo contradicts itself on how much *inference* a reader does when naming the justification
for a surviving answer. **Appendix G.2:** readers do *less* than logic — a size-1 witness fiber
(verdict forces the reason) is not recovered (grok 2/13). **Appendix I.3 / budgetline:** readers do
*more* than string retrieval — they recover the culprit by elimination over the disclosed candidate
set (α up to 1.20). Both hold if read-time recovery is a fixed shallow depth. This experiment finds
where that depth stops, over four derivability classes:

| class | culprit is recoverable by | designed floor |
|---|---|---|
| (a) UNDERIVABLE | nothing (no policy values in notes) | ~1/3 guess |
| (b) ELIM | absence-spotting / eliminate the 2 present passers | ~1/3 guess |
| (c) ARITHMETIC | one `base ± offset` computation (nothing absent; 2 candidates expression-encoded) | ~1/2 guess |
| (d) RETRIEVAL | read the failing value directly | ~1.0 (control) |

## Verdict: the "retrieval-not-inference" reading is REFUTED — readers DO compute

**Headline B fired, not headline A.** The preregistered depth-boundary (P-RIB-2/3) *failed* on all
three models because arithmetic recovery is well above the guess floor — models deploy read-time
computation. P-RIB-5 confirms the arithmetic was within capacity, so this is a *deployment* result,
not a capacity limit.

### Main run — predictions per model (recovery on WHICH, Wilson 95% CI)

| model | (a) underiv | (b) elim | (c) arith | (d) retr | direct-arith | P-RIB-2 (c≤.50) | P-RIB-5 (arith cap) |
|---|---|---|---|---|---|---|---|
| grok | 0.333 | 0.850 | **0.650** [.52,.76] | 1.000 | 0.883 | **FAIL** | PASS |
| gpt | 0.250 | 1.000 | **0.650** [.52,.76] | 1.000 | 0.933 | **FAIL** | PASS |
| haiku | 0.200 | 0.967 | **0.933** [.84,.97] | 1.000 | 0.883 | **FAIL** | PASS |

Prediction-by-prediction (all three models unless noted):
- **P-RIB-0** retrieval control recovery(d) ≥ 0.85 — **PASS 3/3** (all 1.000).
- **P-RIB-1** elimination recovery(b) ≥ 0.75 — **PASS 3/3** (0.85 / 1.00 / 0.97).
- **P-RIB-2** arithmetic fails recovery(c) ≤ 0.50 — **FAIL 3/3** (0.65 / 0.65 / 0.93).
- **P-RIB-3** depth boundary (b−c ≥ 0.25 AND CI-separated) — **FAIL 3/3** (gpt gap 0.35 but c is
  high; grok gap 0.20; haiku gap 0.03).
- **P-RIB-4** elimination genuine (a ≤ 0.50 AND b.ci_lo > a.ci_hi) — **PASS 3/3**. Elimination is
  real: it sits far above the underivable-guess floor on every model.
- **P-RIB-5** arithmetic in capacity (direct ≥ 0.85) — **PASS 3/3** (0.88 / 0.93 / 0.88). The (c)
  shortfall vs (d) is a *deployment* gap, not inability.

### The confound we found and closed (why c2 exists)

A mechanical leak audit (`leak_audit`) showed the main-run class-c is solvable up to **0.84** by a
**base-only heuristic** (read whether the stated *baseline* already fails, ignore the offset). So
the main recovery(c) cannot by itself prove computation. Two facts argued it was genuine anyway:
recovery was equal in base-ambiguous vs base-decisive cells (grok 0.64/0.61, gpt 0.79/0.56, haiku
0.93/0.93), and traces show explicit computation (`97 + 25 = 122 > 100`). **class-c2** removes the
leak by construction — both arithmetic baselines sit on the *pass* side, so only computing the
offset reveals the culprit (base-only recovery forced to 0.000, verified mechanically).

### c2 behavior observed; confirmatory interpretation VOID after guard audit

**Audit correction (2026-07-09).** The preregistration also required first-order surface
features to remain within their frozen balance interval. The committed c2 corpus violates the
offset-magnitude guard: the culprit has the larger offset on 46/60 items (0.7667), outside the
allowed 0.35–0.65 range. `selfcheck_c2` originally removed every shared-checker issue whose first
field started with `CORPUS`; that accidentally removed the `CORPUS-C` surface failure along with
the inapplicable class-size messages. The checker and regression test now preserve this failure.

The cached outputs below remain real observations on the generated corpus, but the confirmatory
campaign is **VOID** under the repository's evidence rules. A no-arithmetic “choose the larger
offset” heuristic scores 46/60 = 0.7667, above the Grok and GPT recovery rates. Haiku's 0.983 is
suggestive, not clean confirmation. A newly generated c3 corpus with all frozen surface baselines
balanced is required before restoring a confirmatory claim.

| model | recovery(c2) | 95% CI | P-C2-1 (≥.60) | P-C2-2 (ci_lo>.50) |
|---|---|---|---|---|
| grok | 0.650 | [.524,.758] | PASS | PASS |
| gpt | 0.733 | [.610,.829] | PASS | PASS |
| haiku | 0.983 | [.911,.997] | PASS | PASS |

- **P-C2-1** recovery(c2) ≥ 0.60 on ≥2/3 models — **PASS (3/3)**.
- **P-C2-2** c2.ci_lower > 0.50 on ≥2/3 — **PASS (3/3)**.
- **P-C2-3** residual base-only leak ≤ 0.34 — **PASS** (0.000 by construction).

**Corrected conclusion:** the main run and explicit traces remain exploratory evidence that
readers can perform one-step arithmetic recovery, and the c2 cached behavior is reusable as
`OBSERVED`. The frozen confirmatory claim is **VOID**, so the strong cross-model arithmetic
deployment conclusion is not established until a balanced c3 rerun beats every preregistered
surface heuristic.

## What this changes

- **The clean arithmetic claim is open.** Candidate elimination still demonstrates that the read
  channel is not string retrieval alone, but c2 does not isolate arithmetic from frozen surface
  heuristics.
- **A c3 balance-first rerun comes before a deeper ladder.** Freeze direction, magnitude, base
  ordering, lexical order, candidate position, and shallow metadata baselines; make model recovery
  beat the strongest baseline by a preregistered paired margin.
- **String loss remains only a lower bound on possible reconstruction.** Explicit arithmetic
  traces show a mechanism worth testing, not a clean cross-model rate.
- **Model heterogeneity remains descriptive.** Haiku's 0.983 on c2 is suggestive, while Grok/GPT
  do not beat the 0.7667 larger-offset heuristic.

## Confounds handled (per CLAUDE.md checklist)

1. Salience/verdict leak: notes carry no verdict/threshold language (`selfcheck` VERDICT_WORDS).
2. Last-anchor parse: corrected last-`PARAMETER:` parser; UNMATCHED surfaced (haiku class-a = 25
   honest refusals-to-guess, correctly counted as non-recovery).
3. Candidate disclosure: DISCLOSED, stated — this is the deployed-J quantity (I.3).
4. Arithmetic correctness + margins ≥ 15% and single culprit were checked. The c2 base-only leak
   was forced to chance, but the shared surface-balance failure was accidentally filtered before
   spend; the confirmatory campaign is therefore VOID.

## Files

`prereg_reader_inference_boundary.md`, `prereg_c2_confirmatory.md`, `gen_items.py` (a/b/c/d),
`gen_c2.py`, `items.jsonl` (240), `items_c2.jsonl` (60), `runner.py` (smoke/run/score + c2),
`responses_raw.jsonl`, `reader_inference_boundary_results.json`,
`reader_inference_boundary_c2_results.json`.
