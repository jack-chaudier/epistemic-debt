# Distill-parity campaign — 2026-07-08

**Status: STEP 1 (local build) COMPLETE 2026-07-08. G1 leak audit PASS (mean AUC 0.5064,
folds 0.4738–0.5315, threshold 0.60 — no regeneration needed). All corpora generated,
selfchecks clean, 50/50 balanced; 3-item smoke through every battery's prompt construction
inspected. Nothing trained, no pod spend yet.**
Plan: `PLAN.md`. Prereg: `prereg_distill_parity.md` — **FROZEN at commit d24e198**; thresholds
pinned by `tests/test_distill_parity_prereg.py`. Two students distilled from the same Qwen3-8B
teacher, differing only in trace content (verdict-only vs verdict+witness fusion register);
parity-matched, Δ-separated, shift-tested (full-doc counterfactual = the weight-borne headline).

## Files

- `gen_items.py` — all corpora (seed family 812xxx, fresh); writes train_pool / parity_gauge /
  dev_slice / delta_battery / delta_reserve / arm3 + `corpus_manifest.json`.
- `leak_audit.py` — G1 surface-leak gate (masked-numerics logistic regression, 5-fold CV);
  committed BEFORE the final pool was generated, per the campaign rules.
- `trace_builder.py` — teacher_raw.jsonl → G2/G3/G4 → `train_V.jsonl` / `train_J.jsonl` +
  `gate_manifest.json` (STOP exits on the frozen gate conditions).
- `runner.py` — smoke + every battery against pod-local vLLM (thinking off, temp 0,
  idempotent cache, hard cap; Arm 3a probes are format-neutral bare ANSWER lines).
- `build_capability.py` — pod-side 250 GSM8K + 250 MMLU slice (seeded).
- `train_distill.py` — frozen QLoRA config, per-epoch checkpoints, identical across conditions.

## GPU session log (rule 3 — every session, no exceptions)

| date | pod id | GPU | $/hr | hours | purpose | $ |
|---|---|---|---|---|---|---|
| — | — | — | — | — | none yet | 0.00 |

**Cumulative GPU spend: $0.00.** API spend: $0.00 (all inference is pod-local).

## Step-0 note (pre-existing pod)

Pod `8huucke042ftjo` (EXITED, 200GB volume, created 2026-07-08) could not be started for
inspection — RunPod host reports no free GPUs (two attempts). Not deleted uninspected; retry at
each session boundary.

## Verdict

Pending.
