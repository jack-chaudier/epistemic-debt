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
| 2026-07-08 | nmzb9ecrnq2gwb | H100 80GB SXM (AP-IN-1, secure) | 2.99 | 0.36 (21:24–21:46 UTC) | deps + vLLM + 12,000 teacher trace calls | 1.07 |

**Cumulative GPU spend: $1.07.** API spend: $0.00 (all inference is pod-local).
Pod stopped (not deleted) at the STOP boundary; volume + HF cache persist for restart.

## STOP 2026-07-08 21:46 UTC — G3 floor breached (1,586 < 3,000), awaiting lead decision

- G2: ops_incident dropped (teacher_v 0.826 < 0.85); ci 0.882 / clinical 0.903 / loan 0.854 /
  sec 0.870 / vendor 0.880 kept (1 dropped ≤ 2, no stop).
- G3 on 5,000: APPROVED survive 0.785; **DENIED survive 0.317** — the J-request flips the
  teacher's own verdict on DENIED items (j_verdict_ok 0.427 vs v_ok 0.784), and a further
  slice names the right parameter without quoting the reading (register non-compliance).
- G4 balances to min side: 793/side → 1,586.
- Observation (not a claim): demanding fused justification degrades the teacher's DENIED
  verdict accuracy by 0.36 — justification-interference in the teacher itself.

## Step-0 note (pre-existing pod)

Pod `8huucke042ftjo` (EXITED, 200GB volume, created 2026-07-08) could not be started for
inspection — RunPod host reports no free GPUs (two attempts). Not deleted uninspected; retry at
each session boundary.

## Verdict

Pending.
