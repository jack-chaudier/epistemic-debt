# B4 training plan — calibrated-reader fine-tune

Two concrete options to turn `dataset_train.jsonl` / `dataset_eval.jsonl` (5,021 / 885 chat
examples, split by item) into a reader that emits the calibrated debt-acknowledgment phenotype.
**Nothing here has been run** — the lead authorizes spend separately. Costs are estimates with
pinned pricing that must be re-verified.

## Shared eval protocol (before / after — same for both options)

The benchmark is the **existing dissociation battery**, run over the held-out `dataset_eval.jsonl`
items (162 items, never seen in training):

1. **Δ (the dissociation gap)** — decision-channel accuracy on witness-**retained** cells minus
   accuracy on witness-**lost** cells, measured against the *calibrated* target (conservative
   DENIED + flag counts as correct on lost cells, not raw item truth). Headline: Δ shrinks toward 0.
2. **Incoherence rate** — fraction of DENIED-decision + `PARAMETER: NONE`-no-failure
   self-contradictions on lost cells (the grok/gpt 0.79→ signature). Target: → 0.
3. **Coherent debt-acknowledgment rate** — `NONE_MISSING_DATA` + explicit missing-data flag over
   all lost-cell NONE responses (haiku native 0.79). Target: → ~1.0.
4. **Fusion-register compliance** — of witnessed golds, fraction whose answer cites the deciding
   value in-clause; of unwitnessed, fraction that carry a `[MISSING DATA]` flag and no
   unwitnessed confidence. Target: high on both.
5. **Guard: retained-cell accuracy must not fall** — the tune must buy calibration without losing
   the ability to answer when the witness *is* present (no over-abstention).

Score with the same corrected parser + `retained()` classification the campaigns use; a semantic
dual-judge (rescore `judge.py`) on the NONE split is the confirmatory instrument for headline (2)/(3).
Report before/after per metric with Wilson CIs; preregister the thresholds before the run.

## Option A — OpenAI fine-tune of `gpt-4.1-mini`

- **Script:** `launch_openai_ft.py` (runnable; `--dry-run` prints the estimate and projects
  `dataset_*.openai.jsonl` messages-only files; `--go` uploads + creates the job). The `meta`
  block is stripped at upload.
- **Config:** base `gpt-4.1-mini-2025-04-14`, `n_epochs=3`, validation file = eval split, suffix
  `calib-reader-b4`.
- **Cost (pinned 2026-07-08 — VERIFY):** ~1.62M training tokens/epoch × 3 = **~4.86M tokens** at
  $5.00/1M → **≈ $24** training. Fine-tuned inference $0.80/1M in, $3.20/1M out; the before/after
  battery is ~1k probe calls at ~350 tok each ≈ 0.7M tokens → **< $2**. **Total ≈ $25.**
- **Pros:** zero infra, hosted inference, deterministic-ish at temperature 0, drops straight into
  the existing `providers.chat` harness for the battery. **Cons:** closed weights (no J-lens /
  tuned-lens internal witness probe — the B4 stretch goal needs open weights); per-call inference
  cost; you are tuning a model already strong on this task, so headroom is smaller than on a weak
  open model.

## Option B — open-weight QLoRA on a Qwen3-4B-class reader

- **Model:** `Qwen/Qwen3-4B-Instruct` (or Llama-3.2-3B-Instruct). Small enough for a single
  consumer GPU under 4-bit QLoRA; open weights unlock the **internal witness probe** (tuned-lens /
  logit-lens arm — is the destroyed witness computed-but-unverbalized or truly gone?), which is
  the second half of the B4 charter.
- **Config:** ready-to-run axolotl config committed as `qlora_qwen3_4b.yaml` (below). TRL
  equivalent: `SFTTrainer` with `packing=True`, `LoraConfig(r=16, alpha=32, dropout=0.05,
  target_modules=q,k,v,o,gate,up,down)`, 4-bit nf4, `chat_template` applied to the `messages`
  field (drop `meta` first).
- **Hardware / cost:** 5,021 examples × ~322 tok ≈ 1.6M tok/epoch; 3 epochs of 4-bit QLoRA on a
  4B model ≈ **1–2 GPU-hours on one A100-40GB / RTX 4090-24GB**. Rented (~$1.5–2.5/hr for a 4090,
  ~$1.8/hr A100 spot) → **≈ $2–5**. Local GPU → ~free + electricity. Peak VRAM ~14–18 GB at
  seq-len 1024, micro-batch 4 + grad-accum.
- **Pros:** cheapest; owns weights; enables the internal-probe arm and the B5c writer-side
  register objective; unlimited local inference for the battery. **Cons:** you run the infra;
  4B base is weaker, so retained-cell accuracy (eval guard 5) must be watched closely.

### `qlora_qwen3_4b.yaml` (axolotl)

```yaml
base_model: Qwen/Qwen3-4B-Instruct
load_in_4bit: true
strict: false
chat_template: qwen3
datasets:
  - path: ./dataset_train.jsonl        # strip the top-level `meta` key first (jq 'del(.meta)')
    type: chat_template
    field_messages: messages
test_datasets:
  - path: ./dataset_eval.jsonl
    type: chat_template
    field_messages: messages
    split: train
dataset_prepared_path: ./last_run_prepared
sequence_len: 1024
sample_packing: true
pad_to_sequence_len: true
adapter: qlora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
gradient_accumulation_steps: 4
micro_batch_size: 4
num_epochs: 3
optimizer: adamw_bnb_8bit
lr_scheduler: cosine
learning_rate: 0.0002
bf16: auto
gradient_checkpointing: true
warmup_ratio: 0.03
logging_steps: 10
saves_per_epoch: 1
weight_decay: 0.0
special_tokens: {}
```

Prep step (both frameworks want messages-only): `jq -c 'del(.meta)' dataset_train.jsonl > train.msgs.jsonl`.

## Recommendation

Run **Option B first** (~$2–5): cheapest, owns the weights, and it is the only path that unlocks
the internal witness probe named in the B4 charter. Use **Option A** as the strong-baseline
comparison — if a hosted `gpt-4.1-mini` tune still shows residual Δ or incoherence, that bounds how
much of the phenotype is trainable vs architectural. Preregister the eval thresholds (Section top)
before either run.
