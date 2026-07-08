# Preregistration — B4 calibrated-reader QLoRA eval (frozen 2026-07-08, before training)

Training: local MLX QLoRA (`mlx/lora_config.yaml`, frozen alongside this file) of
`Qwen3-4B-Instruct-2507-4bit` on `dataset_train.jsonl` (5,021 examples, 2 epochs, rank 16).
Eval: the shared protocol from `training_plan.md`, before (base model) vs after (base+adapter),
on the 885-example held-out `dataset_eval.jsonl` (162 items never seen in training), scored with
the corrected last-anchor parser and `retained()` classification. Lost-cell decision correctness
is scored against the **calibrated target** (conservative DENIED + missing-data flag), per the
DATASET_CARD gist-trap note.

## Predictions (frozen thresholds; each reported pass/fail)

- **P-B4-1 (gap closes):** Δ_after ≤ 0.5 · Δ_before, where Δ = retained-cell decision accuracy −
  lost-cell calibrated decision accuracy.
- **P-B4-2 (incoherence dies):** lost-cell incoherence rate (decision=DENIED + WHICH asserts
  no-failure) after ≤ 0.05.
- **P-B4-3 (coherent debt acknowledgment):** lost-cell coherent missing-data acknowledgment rate
  after ≥ 0.75 (haiku's native rate, 0.79, is the bar to approach; base Qwen expected ≪).
- **P-B4-4 (fusion-register compliance):** on witnessed eval cells, ≥ 0.75 of answers cite the
  deciding value in-clause; on lost cells, ≥ 0.75 carry an explicit missing-data flag.
- **P-B4-5 (no over-abstention guard):** retained-cell decision accuracy after ≥ before − 0.05.

Campaign reading: the tune is a success iff P-B4-1 AND P-B4-5 pass and at least two of
P-B4-2/3/4 pass. Anything else is reported as the split/failure it is.

## Cost

Training: $0 API (local Apple-Silicon compute). Eval: $0 API (local generation, both checkpoints).
