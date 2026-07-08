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
| 2026-07-08 | a17mckiju6mrk6 | H100 80GB SXM (AP-IN-1, secure) | 2.99 | session open 21:54 UTC | probe (500) + regen traces (19,000) + 2× student QLoRA + evals | TBD at stop |

Note: nmzb9ecrnq2gwb could not restart after the STOP pause (host GPU taken — the stop/start
trap); volume held nothing unique (teacher_raw committed, venv/HF-cache rebuildable), deleted
and re-provisioned as a17mckiju6mrk6 with a scripted setup.

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

## Step-0 note (pre-existing pod) — RESOLVED

Pod `8huucke042ftjo` (EXITED, 200GB volume) was never startable for inspection (host full,
4 attempts over ~2.5h) and disappeared from the account at ~23:15 UTC — deleted outside this
session (console). Repo evidence indicated the volume held only uploads reproducible from the
repo (no committed remote adapter, no completed remote training log). Nothing retrieved.

## Revision-1 resolution (2026-07-08, ~22:30 UTC)

The frozen revision protocol resolved the STOP: probe DENIED joint-survival **0.796** vs the
0.55 gate (J-verdict on DENIED 0.427 → **1.000**). Regenerated pool: 5 kept domains × 1,900 =
9,500 (5,000 ids byte-identical to the committed original). Gates on r1: **G2 0 dropped**
(clinical 0.901, ci ✓, vendor 0.874, sec 0.873, loan 0.857); **G3** v_wrong 1,158 /
j_verdict_wrong 23 / j_witness_wrong 43 / **j_unsound 81** (the right-for-wrong-reasons
sub-check; ~1% of J-correct items, dropped) → 8,195 survivors; **G4 → 7,272** balanced
examples (floor 3,000). Soundness caveat: reading+threshold quoting verified on every trace;
explicit pass/fail direction language present in ~40% of policy clauses (15,068 unverifiable
clauses counted, not dropped). **G1 re-audit on the r1 pool: AUC 0.4932 — chance.** With the
J channel at ceiling, the retained set is conditioned on *bare-channel* competence (the more
benign direction — the corpus keeps items the teacher can decide without help). Training fired
on these numbers per the lead's rule.

## OBSERVED row candidate (frozen note — logged, not chased)

**Verdict–justification ordering interference in the teacher.** Same model (Qwen3-8B, temp 0,
thinking off), same synthetic review items, three prompt orderings, three DENIED-side verdict
accuracies: bare ANSWER **0.784** (n=2,500 kept-domain pool; 0.800 on the 500-item probe
slice), justify-with-verdict-first (r0 fusion register) **0.427** (n=2,500), quote-evidence-
then-verdict (r1 register) **1.000** (n=250 probe slice, seed 813000). A 0.57 swing on
ordering alone; asking for justification *before* the verdict destroys DENIED accuracy,
demanding evidence *first* beats the bare channel. Mechanism unresolved (emission garbling vs
genuine decision interference) — verdict-then-justify vs justify-then-verdict micro-experiment
queued in NEXT.md; no campaign GPU spent on it. Provenance: `gate_manifest.json` (r0 run,
git history at ea7cae7), `probe_results.json`, `revision_protocol.md`.

## Verdict

Pending.
