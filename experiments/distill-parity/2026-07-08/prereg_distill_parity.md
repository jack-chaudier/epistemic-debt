# Preregistration — distillation parity run (freeze on commit, before any GPU/API spend)

Design: `PLAN.md` (same directory). One manipulated variable: trace content. Teacher
`Qwen/Qwen3-8B`, students `Qwen/Qwen3-1.7B` QLoRA (r=16, α=32, dropout 0.05, all-linear
targets, 3 epochs, lr 2e-4 cosine, seq 1024, seeded) — identical configs across conditions.
Student-V trains on verdict-only traces; Student-J on fusion-register verdict+witness traces.
Qwen3 thinking mode pinned OFF in all trace generation and all eval inference; `<think>` blocks
stripped before parsing. Temperature 0 everywhere; idempotent response cache keyed
(item, call-type, model); hard call cap per battery.

## Frozen pipeline gates (applied before training; each reported)

- **G1 — surface-leak audit:** logistic regression on train-pool document surface features with
  policy-relevant numerics masked, predicting the verdict, 5-fold CV. If held-out AUC ≥ 0.60,
  the pool is regenerated with tightened draws and the audit re-run; the final pool's AUC is
  reported. Training may not start on a pool that fails G1.
- **G2 — teacher inclusion gate:** per corpus, teacher full-document verdict accuracy ≥ 0.85
  (thinking off). Corpora below the gate are dropped before any student is trained or evaluated.
- **G3 — joint trace filter:** an item enters the shared train set iff the teacher's verdict AND
  its named deciding witness are both correct against ground truth. ONE item set for both
  conditions; V-traces and J-traces are built from the same items.
- **G4 — class balance:** train pool fixed 50/50 APPROVED/DENIED after G3 (downsample the
  larger side, seeded).
- **G5 — split hygiene:** all eval sets disjoint from the train pool by item and by seed family;
  Δ-battery cells split by item, never by cell.

## Checkpoint selection rule (fixed here, not post hoc)

Each condition yields 3 epoch-end checkpoints. Selection uses a **dev parity slice** (300
full-document items, disjoint from every confirmatory set): choose the (V, J) checkpoint pair
minimizing |acc_V − acc_J| subject to both ≥ 0.70 on each verdict side of the dev slice. Ties
break toward the later epoch. P-DP-0 is then *confirmed* on the held-out parity gauge — the dev
slice never appears in any reported number.

## Sample sizes (frozen)

- Standard parity gauge: ≥ 300 held-out full-document items, verdict-balanced.
- External capability slice: 250 GSM8K + 250 MMLU items, identical prompts/decoding both students.
- Δ battery: ≥ 200 lost-cell and ≥ 200 retained-cell probes per model (teacher, V, J).
- Shift Arm 3a (full-document counterfactual): ≥ 150 items, counterfactual-verdict balanced.
- Shift Arm 3b (compressed-artifact counterfactual): ≥ 90 items (row-27 shape), with the
  original-accuracy guard ≥ 0.70 on BOTH verdict sides of the source artifacts (non-negotiable
  for citing 3b).
- All intervals: Wilson 95%. UNMATCHED/anomaly counts surfaced in every results JSON.

## Predictions (each reported pass/fail; thresholds frozen)

- **P-DP-0 (parity precondition):** |acc_V − acc_J| ≤ 0.05 on the held-out parity gauge, both
  ≥ 0.70 on both verdict sides, AND |acc_V − acc_J| ≤ 0.05 on the external capability slice.
  If P-DP-0 fails after the checkpoint rule above, the headline comparison is **VOID** and is
  reported as such (the accuracy-vs-Δ scatter is still published, labeled exploratory).
- **P-DP-1 (Δ separation):** Δ_V − Δ_J ≥ 0.15 with non-overlapping Wilson 95% CIs, where
  Δ = retained-cell − lost-cell calibrated decision accuracy on the dissociation battery.
- **P-DP-2 (witness channel):** Student-J witnessed-cell WHICH accuracy ≥ Student-V + 0.20;
  Student-V lost-cell incoherence rate ≥ 2× Student-J's. WHICH and phenotype channels are
  scored by the corrected last-anchor parser AND a semantic dual-judge (rescore `judge.py`
  pattern, agreement reported); the dual-judge is the confirmatory instrument for phenotype.
- **P-DP-3a (weight-borne debt — headline):** full-document counterfactual re-policy:
  error_V − error_J ≥ 0.15. The full document is in context, so the gap can only be in the
  weights.
- **P-DP-3b (artifact-borne cross-check):** compressed-artifact counterfactual:
  error_V − error_J ≥ 0.15 on witness-absent items and ≤ 0.05 on witness-present items.
- **P-DP-4 (calibration curve — descriptive only):** report Spearman ρ of Δ(t0) vs
  shift-failure rate over (corpus × condition × budget) cells plus the realdoc held-out point,
  with the fitted curve. No pass/fail; cells share models and are not independence-clean.
- **P-DP-5 (DPI across the training boundary — WHICH-lost only):** each student's WHICH-lost
  recovery ≤ teacher's WHICH-lost + the teacher CI half-width, per corpus. Explicitly NOT
  stated on Δ: Student-J is trained toward calibrated lost-cell abstention, so Δ_J below the
  teacher's is a success mode, not a violation.

## Campaign reading (frozen)

The run is a **confirmation** iff P-DP-0 passes AND P-DP-1 AND P-DP-3a pass. P-DP-2, P-DP-3b,
and P-DP-5 are reported individually and modulate the interpretation, not the verdict.

**Negative branch (pre-committed):** if P-DP-0 passes and P-DP-1 or P-DP-3a fails, the recorded
result is "final-answer distillation does not manufacture measurable epistemic debt on this task
family at this scale" — a REFUTED-direction entry for the training-boundary generalization of
Law 1, entered in RESULTS.md with the same prominence a confirmation would get.

**Conditional commitment:** if P-DP-1 AND P-DP-3a pass, the logit-lens/tuned-lens witness probe
on Student-V lost-witness items (computed-but-unverbalized vs truly absent) is run before the
campaign is written up — it is part of this campaign, not future work.

## Cost

GPU: est. $29–48 (H100 SXM, ~12–16 GPU-h; logged per session in the README like API costs).
API: ~$0 (all open-weight on-pod); ≤ $1 if a hosted model serves as the second dual-judge.
