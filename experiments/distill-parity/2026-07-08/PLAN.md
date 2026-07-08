# Distillation parity run ("the two-model demo") — campaign plan, 2026-07-08

**Status: PLAN, revised after design review 2026-07-08 — nothing has been run.** The prereg
(`prereg_distill_parity.md`, same directory) freezes on commit, before any GPU or API spend, per
CLAUDE.md. Review fixes incorporated: P-DP-5 restated on the WHICH-lost channel only (the Δ
version would have fired falsely on the success case); the shift eval split into full-document
(weight-borne, the headline) vs compressed-artifact (supporting) arms; a surface-leak audit
gates the train pool against SGD shortcut-mining; joint verdict+witness trace filter; external
capability-parity slice; N ≥ 200/cell power; 50/50 train balance; Qwen3 thinking mode pinned
off. Claims live in `results/RESULTS.md` only.

## The claim being tested

Law 1 generalized past the context boundary: **every compression boundary in the pipeline
manufactures the same debt** — the optimizer keeps the verdict because the verdict is what the
loss paid for, and drops the justification because nothing paid for it. Distillation is the
cheapest training-time boundary to instrument with weights we control.

The extractable artifact: **two students distilled from the same teacher, matched on every
standard accuracy metric, separated by Δ — and Δ predicts which one breaks under distribution
shift.** Accuracy is a lagging indicator; Δ is a leading one. If it holds, confabulation at the
model boundary and witness loss at the compaction boundary are one phenomenon with one meter.

**Honest falsification branch (preregister it):** distillation may preserve justification fine —
teachers emit reasons and students imitate them, so the verdict-only condition may not produce
benchmark-parity in the first place, or Δ may not separate. Either failure is a genuine negative
result: "the feared failure mode does not exist at the model boundary," and the program retreats
to the context boundary where it is already solid. Asymmetric bet; report whichever branch fires.

## Why a controlled fine-tune beats the API model-ladder (queue item 6)

The market ladders (gpt-4.1→mini→nano, sonnet→haiku) confound distillation with pretraining
scale, data, and RLHF differences. Row 27's pilot also showed the guard problem: cached source
artifacts were too weak on ordinary accuracy. Training our own pair removes both confounds:

- Same base model, same training items, same optimizer, same token budget. The ONLY manipulated
  variable is **what the distillation traces carry** — verdict-only vs verdict+witness.
- We can *engineer* benchmark parity (the hard precondition) by training both students to the
  same accuracy criterion, instead of hoping the market pair happens to be matched.
- Open weights unlock commitment #3: the mechanistic correspondence test (logit-lens/tuned-lens —
  is the witness computed-but-unverbalized, or gone?).

The off-the-shelf ladder survives as a cheap exploratory arm (Arm C below), not the headline.

## Design

### Models

| role | model | why |
|---|---|---|
| Teacher | `Qwen/Qwen3-8B` (instruct) | strong enough to be near-ceiling on our corpora; bf16 fits one 80GB card with vLLM |
| Student-V | `Qwen/Qwen3-1.7B` + QLoRA, trained on **verdict-only** teacher traces | the condition where the loss pays only for the answer channel |
| Student-J | `Qwen/Qwen3-1.7B` + QLoRA, trained on **verdict+witness (fused)** teacher traces | identical compute, loss also pays for justification |
| (optional) Student-V/J at 4B | same two conditions at `Qwen3-4B` | size ladder — does debt grow with compression ratio? run only if budget allows |

Trace formats:
- **V-traces:** teacher answers `DECISION: <verdict>` only (final-answer distillation — the
  industry-default cheap recipe).
- **J-traces:** teacher answers in the fusion register (row 30 contract): verdict + deciding
  value in the same clause, `PARAMETER:` witness line, missing-data flag when unwitnessed.
  Reuses the B4/ft-dataset gold-templating conventions rather than free-form CoT, so scoring
  stays parser-compatible.

**Qwen3 thinking mode is pinned OFF everywhere** (`enable_thinking=False` / `/no_think`) — in
teacher trace generation AND all eval inference for teacher and students alike — and any stray
`<think>` block is stripped before parsing. Unpinned, the teacher leaks variable reasoning
traces into V-traces (free CoT contaminating the verdict-only condition, i.e. quietly destroying
the manipulated variable) and think-block garbage hits the parsers.

Same items, same count, same epochs, same LoRA config for both students. Token-count asymmetry
(J-traces are longer) is disclosed and handled by matching *optimizer steps and examples*, not
tokens; a token-matched sensitivity arm (V gets proportionally more examples) is the robustness
check if P-DP-2 passes.

### Corpora & splits

- **Train pool:** items from `experiments/lib/domains.py` generators (6 schemas), fresh seeds,
  disjoint-by-item from every eval set, **balanced 50/50 APPROVED/DENIED** (row 31's crash→DENY
  reflex is the warning: a skewed pool trains a prior, not a policy; parity is gauged per
  verdict side, so training mirrors it). Teacher labels generated on-pod ($0 API). Target ~4–6k
  traces per condition. **Joint filter defining ONE item set used by both conditions:** keep an
  item iff the teacher's verdict AND its named witness are correct against ground truth — a
  verdict-only filter would let Student-J silently train on a cleaner subset (and on
  confabulated reasons); the conditions must stay item-identical.
- **Surface-leak audit (pre-training gate):** the domains.py confound guards were built against
  compaction, not against SGD spending thousands of gradient steps mining any surface regularity
  that predicts the verdict. Before training, fit a dumb classifier (logistic regression on
  document surface features with the policy-relevant numerics masked) on the train pool; if it
  beats chance materially (threshold frozen in the prereg), regenerate with tightened draws.
  Without this, Student-V can hit parity via the leak and the Δ separation partly measures
  leak-reliance — a confounded version of the right answer.
- **Eval, standard (parity gauge):** held-out full-document decision battery — the "benchmark"
  both students must match on. Split by item, never by cell. **Plus an external capability
  slice** (a few hundred GSM8K/MMLU items, both students, on-pod, ~1 GPU-h): parity on the
  in-house battery alone invites "you engineered parity on one narrow family"; matching on a
  generic slice hardens the claim from benchmark-parity to capability-parity.
- **Eval, Δ battery:** the existing dissociation protocol (`experiments/lib/dissociation.py`) —
  witness-retained vs witness-lost compressed artifacts, decision + WHICH + abstention probes,
  corrected last-anchor parser, Wilson CIs, UNMATCHED counts surfaced. **Powered by
  construction:** P-DP-1 demands a 0.15 gap with non-overlapping 95% CIs, so size N ≥ 200
  lost-cell probes per condition (highpower scale; below ~150/cell the CIs are ±0.08 and the
  test is underpowered against its own threshold). Eval inference is on-pod and nearly free —
  there is no reason to run this small.
- **Eval, shift — two preregistered arms; they isolate different debts:**
  - **Arm 3a, full-document counterfactual (the novel finding — weight-borne debt):** new policy
    over originally non-policy readings, probed with the FULL document in context. Nothing is
    missing from the artifact, so any V−J failure gap is debt **in the weights**: Student-V,
    paid only for verdicts, internalized policy-specific shortcuts; Student-J, paid for locating
    and verbalizing the deciding value, re-computes under the new policy. This is Law 1 at the
    training boundary and carries the headline.
  - **Arm 3b, compressed-artifact counterfactual (supporting arm — artifact-borne debt):** the
    transfer-law design (`experiments/transfer-law/2026-07-08/gen_items.py` pattern) with the
    row-27 guard fix: source artifacts must clear ordinary accuracy ≥ 0.70 on BOTH verdict
    sides (value-dense / looser-budget artifacts; keep the source-verdict split analysis). On
    its own this arm would only restate the existing artifact result on a new model — it rents
    the machinery and cross-checks 3a; it cannot carry the distillation claim.
- **Eval, real prose:** the realdoc NTSB corpus (row 31) as the external-validity arm.

Confound checklist applies (CLAUDE.md): last-anchor parser only, semantic dual-judge on any
phenotype channel, candidate-set disclosure decided and stated per probe, smoke 3 items
end-to-end before full spend.

### Preregistered predictions (thresholds to freeze in the prereg file)

- **P-DP-0 (parity precondition):** Student-V and Student-J standard full-doc decision accuracy
  within 0.05 of each other, both ≥ 0.70 on both verdict sides, AND within 0.05 on the external
  capability slice. If parity fails after the budgeted tuning attempts, the headline comparison
  is VOID — report as such.
- **P-DP-1 (Δ separation):** Δ(Student-V) − Δ(Student-J) ≥ 0.15 with non-overlapping 95% CIs,
  where Δ = retained-cell − lost-cell calibrated decision accuracy on the dissociation battery
  (N ≥ 200 lost-cell per condition).
- **P-DP-2 (witness channel):** Student-J WHICH-accuracy on witnessed cells ≥ Student-V + 0.20;
  Student-V lost-cell incoherence ≥ 2× Student-J's.
- **P-DP-3a (weight-borne debt — THE headline):** full-document counterfactual re-policy, all
  values in context: error(V) − error(J) ≥ 0.15. Nothing is missing from the artifact, so the
  gap can only live in the weights — Law 1 at the training boundary, and the leading-indicator
  claim (the standard benchmark saw two identical models).
- **P-DP-3b (artifact-borne cross-check):** on compressed artifacts, error(V) − error(J) ≥ 0.15
  on witness-absent items and ≤ 0.05 on witness-present items (row-27 machinery, guard fixed).
- **P-DP-4 (calibration curve — descriptive, not confirmatory):** pooling (corpus × condition ×
  budget) cells, Δ at t0 vs shift-failure rate, report Spearman ρ and the fitted curve with the
  realdoc arm as one held-out point. Cells share models, so ρ is not independence-clean; P-DP-3a
  carries the confirmatory weight, this carries the figure.
- **P-DP-5 (DPI across the training boundary — WHICH channel only):** on destroyed artifacts,
  each student's WHICH-lost recovery ≤ teacher's + CI. This is the data-processing-inequality
  claim (no student recovers witness information the artifact doesn't contain), stated on the
  channel the theory actually protects. NOT stated on Δ: Δ is partly reader policy, and
  Student-J is trained toward better lost-cell calibration, so a successful J-student can
  legitimately show Δ below the teacher's — the earlier "students' Δ ≥ teacher's" version would
  have fired falsely on the success case.

Exploratory (labeled as such): the 4B size ladder; Arm C off-the-shelf ladder
(Qwen3-32B/8B/4B/1.7B stock instruct, inference-only Δ sweep); logit-lens correspondence.

### Mechanistic grounding (commitment #3 — one test, not a program; MANDATORY if P-DP-1 and
P-DP-3a pass, not a slip-able stretch goal)

On Student-V lost-witness items where the verdict is right and WHICH fails: logit-lens /
tuned-lens probe for the destroyed witness token at intermediate layers. Two outcomes, both
reportable: computed-but-unverbalized (workspace/substrate split, J-space vocabulary) vs truly
absent (the debt is in the weights). This is what separates an instrument from a heuristic;
it needs the open weights we will already have on the pod.

## Execution on RunPod

Verified 2026-07-08: MCP authenticated; H100 SXM / H200 / RTX 4090 in high stock; no network
volumes; one EXITED pod (`8huucke042ftjo`, 200GB volume, old cu118 image) — delete it (storage
bills while stopped) unless it holds something.

- **Pod:** 1× `NVIDIA H100 80GB HBM3`, secure cloud, image `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404`,
  container disk 60GB, volume 150GB at `/workspace`, port 22. One card runs teacher vLLM
  inference (8B bf16) and student QLoRA sequentially. Fallback if H100 price offends: A100 80GB.
  (A 4090 CAN run everything 4-bit, but teacher trace-gen throughput and the 32B Arm-C teacher
  want the 80GB card; the whole run is ~a day of GPU time either way.)
- **Workflow** (extends `experiments/ft-dataset/2026-07-08/remote/` runbook; scp + nohup + logs):
  0. **Delete the exited pod `8huucke042ftjo`** (200GB stopped volume = pure storage waste)
     after confirming it holds nothing needed.
  1. Local: `gen_items.py` (train pool + all eval sets, deterministic seeds, 50/50 verdict
     balance), run the surface-leak audit, regenerate if it fires; smoke 3 items.
  2. Pod: vLLM serve teacher (thinking pinned off) → batch-generate V-traces and J-traces
     (~1–2 GPU-h).
  3. Local: apply the joint verdict+witness filter → ONE item set → pack the two SFT sets;
     verify counts and class balance, spot-read 20 traces each.
  4. Pod: train Student-V, Student-J (QLoRA r16, pinned deps from the B4 runbook; ~1–2 GPU-h
     each at 1.7B). Checkpoint each epoch to the volume.
  5. Pod: parity gauge (in-house battery + GSM8K/MMLU slice) on checkpoints; pick per-condition
     checkpoints that satisfy P-DP-0 (this selection rule is IN the prereg, not post-hoc).
  6. Pod: run all eval batteries (standard, Δ at N ≥ 200/cell, shift arms 3a and 3b, realdoc)
     for teacher + both students via local vLLM inference, thinking off, temperature 0,
     idempotent response cache keyed (item, call-type, model) — same contract as API runners
     (~3–5 GPU-h at the powered N).
  7. Retrieve adapters + raw responses; **stop, then delete the pod**; score locally with the
     existing parser/CI stack; dual-judge the phenotype channels.
  8. Stretch: lens probe (can run on a cheap 4090 pod later; adapters are saved).
- **Rider (recommended):** B4 calibrated-reader QLoRA is dataset-ready with a frozen prereg and
  costs ~1–2 GPU-h more on the same pod — run it in the idle window during step 2/6. Separate
  campaign, separate results; it just shares the meter (rental).

## Budget

| item | est |
|---|---|
| H100 SXM ~$2.4–3/hr × ~12–16 GPU-h (traces + 2 trainings + powered evals + capability slice + slack) | $29–48 |
| B4 rider (+1–2 h) | +$3–6 |
| 4B ladder arm (+3–4 h) | +$8–12, only if core passes |
| API spend | ~$0 (all open-weight on-pod); ≤$1 if a cross-vendor judge is used for the dual-judge |
| **Core total** | **≈ $30–50** |

Hard rules: log GPU-hours and $ in the README like API costs; stop the pod at every idle
boundary; never write keys to the pod (training data is synthetic — key-scan test still applies
to retrieved artifacts).

## Deliverables

1. `experiments/distill-parity/2026-07-08/` — prereg, generators, trace-builder, train configs,
   runner (smoke/run/score), raw responses, scored.csv, `distill_parity_results.json`, README
   verdict; regression test pinning headline numbers.
2. RESULTS.md row(s) with honest labels — including the negative-result branch if it fires.
3. Theory appendix: Law 1 at the training-time boundary; Δ as leading indicator.
4. Site: new finding block + Road update ONLY per the evidence rules.
5. The two adapters + eval harness = the seed of the public demo (two benchmark-identical
   models, one meter that tells them apart) — but the demo is downstream, not this campaign.

## Timeline (aggressive but real)

- **Day 1:** prereg frozen + committed; generators + trace format + smoke locally.
- **Day 2:** pod up; traces; both trainings; parity gauge. Pod down overnight.
- **Day 3:** eval batteries on pod; retrieve; score + dual-judge locally.
- **Day 4:** writeup, ledger row, tests; decide on ladder/lens extensions.

## Risks & pre-committed answers

- **Parity never achieved** (V-student can't reach 0.70, or the two can't be matched): bounded
  tuning protocol (≤3 checkpoint/epoch choices per condition, chosen by the prereg rule); if
  still unmatched, report P-DP-0 VOID and publish the accuracy-vs-Δ scatter anyway (exploratory).
- **Student-V mines a surface shortcut to parity:** the pre-training leak audit (masked-numerics
  logistic regression) gates the train pool; if the leak is found post hoc anyway, the Δ
  separation is reported as confounded, not as the result.
- **J-traces leak eval structure:** all eval items disjoint by item AND by seed family; the
  fusion register is a format, not item content.
- **Teacher too weak on a corpus:** drop that corpus pre-registeredly by a teacher-accuracy
  ≥ 0.85 inclusion gate applied BEFORE any student eval.
- **Trace-length confound:** disclosed; steps/examples-matched primary, token-matched
  sensitivity arm secondary.
- **Parser artifacts (incidents #2, #3):** last-anchor parser, UNMATCHED surfaced, semantic
  dual-judge on WHICH and phenotype channels from the start, not as a patch.
