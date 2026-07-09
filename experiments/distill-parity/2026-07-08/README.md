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
| 2026-07-08/09 | a17mckiju6mrk6 | H100 80GB SXM (AP-IN-1, secure) | 2.99 | 2.54 (21:54–00:27 UTC) | probe (500) + regen traces (19,000) + 2× student QLoRA + all eval batteries (25,440 records) | 7.60 |

| 2026-07-09 | adl55jkme0w1a1 | RTX 4090 (EU-RO-1, secure) | 0.69 | 0.30 (00:29–00:47 UTC) | base-model capability control (500 calls) | 0.21 |

Note: nmzb9ecrnq2gwb could not restart after the STOP pause (host GPU taken — the stop/start
trap); volume held nothing unique (teacher_raw committed, venv/HF-cache rebuildable), deleted
and re-provisioned as a17mckiju6mrk6 with a scripted setup.

**Cumulative GPU spend: $8.88. Campaign closed 2026-07-09 00:47 UTC; account holds zero pods.**
API spend: $0.00 (all inference was pod-local). Adapters (all checkpoints, both students)
retrieved to `adapters/` locally (not committed — 1.6GB; regeneration is deterministic from the
committed traces + frozen config).

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

## Verdict (2026-07-09)

**Campaign reading: VOID on the frozen parity precondition — and the exploratory results are
the story.** VOID is the *third* branch, not the pre-committed negative branch: the negative
result ("distillation doesn't manufacture measurable debt") would have required parity to hold
and separation to fail; what happened is that parity itself could not be engineered under the
frozen checkpoint rule (gap 0.064 vs the 0.05 bar; capability slice failed much harder). The
rule fired as written — no relitigating a near-miss. Whether the exploratory findings justify
a second campaign with a revised parity protocol (more checkpoints, parity-targeted early
stop, or token-budget-matched V-traces) is a fresh design question. All numbers in
`distill_parity_results.json`; scored from 25,440 raw responses.

- **P-DP-0 FAIL → VOID.** Held-out parity gap 0.064 (bar 0.05; sv1 0.978 vs sj1 0.914, all
  verdict sides ≥ 0.70) and capability gap 0.144 — **in Student-J's favor** (GSM8K: V 0.152 vs
  J 0.524; MMLU: V 0.492 vs J 0.408). The frozen checkpoint budget was exhausted (dev-slice
  rule, truncation artifact fixed and disclosed; selection (sv1, sj1), dev gap 0.063).
- **Exploratory Δ separation (P-DP-1's numbers, VOID-labeled): Δ_V 0.980 vs Δ_J 0.686,
  separation 0.294, lost-cell CIs non-overlapping.** Mechanism: on witness-lost DENIED cells
  Student-V answers APPROVED 99% of the time (decision_lost 0.011; realdoc 0.000; teacher
  0.596) — verdict-only distillation manufactured **unwitnessed confidence**, the inverse
  valence of row 31's crash→DENY reflex, while *beating* J on the in-domain full-doc gauge.
  Accuracy metrics cannot see it; Δ can. On real NTSB prose: Δ_V 0.875 vs Δ_J 0.154.
- **The training-boundary Law-1 headline did NOT materialize (P-DP-3a fail, honest negative):**
  full-document counterfactual re-policy errors are near-ceiling-low for both students
  (V 0.039, J 0.067, gap −0.028). At 1.7B/synthetic-domain scale, weight-borne re-policy
  brittleness was not detected. P-DP-3b is uninterpretable per the frozen guard: Student-V
  fails the ≥0.70 source-side guard (DENIED-side 0.533) — itself the unwitnessed-confidence
  phenotype. Compliance diagnostic (pre-committed): V bare-compliance 1.00, J 0.00 (all-
  preamble, acc 0.933) — the bare-only split has no J cells, so the weight-vs-inference
  attribution is moot as frozen.
- **P-DP-2 fail** (witnessed WHICH: V 0.632 vs J 0.673 — no +0.20 gap; incoherence ~0 both).
  **P-DP-5 fail-with-confound:** V which_lost 0.313 > teacher 0.080 + CI, but the dissociation
  protocol is self-compressed — each model reads its own artifacts, so this is NOT a DPI
  violation; the artifact-fixed variant is the successor. **P-DP-4 descriptive** Spearman
  −0.71 over 18 cells, uninformative under Arm-3a ceiling compression.
- **Unplanned observation (strong): justification training changes COMPRESSION behavior.**
  As compactors, J retains the deciding witness far more than V (Δ-battery kept-cells 367 vs
  223; Arm-3b cf-witness present rate 0.728 vs 0.333). The J-loss appears to buy a
  witness-preserving writer, not just a calibrated reader.
- **Capability-gap mechanism — hold the weaker claim until the base control lands.** Token
  counts on the capability slice: Student-V emits bare answers (GSM8K median 15 completion
  tokens, MMLU median 5), Student-J reasons before answering (medians 145/143). A model
  trained to emit five tokens failing GSM8K without CoT is the *null hypothesis*, not the
  finding: the gap may be inference-time CoT budget (V learned never to emit reasoning
  tokens), not gutted weights. Base Qwen3-1.7B under identical decoding/prompt is the
  disambiguating control — run as an exploratory diagnostic, prereg untouched. Note the
  confound sign here is the mirror of the Arm-3a preamble warning: the same emission-register
  mechanism would inflate this gap.
- **Base control result (exploratory diagnostic, 2026-07-09, `base_capability_raw.jsonl`):
  the emission-register reading wins.** Stock Qwen3-1.7B, identical prompt/decoding/thinking-
  off: GSM8K **0.516** at median 147 completion tokens (vs J 0.524 @ 145 — statistically
  indistinguishable in accuracy AND token budget), MMLU 0.452 (V 0.492, J 0.408). So
  Student-J did not gain reasoning; it **preserved the base model's natural CoT emission**.
  Student-V's verdict-only SFT suppressed reasoning-token emission (median 15) and deployed
  GSM8K collapsed 0.516 → 0.152. Correct claim strength: verdict-only distillation trains the
  model into *silence*, and the silence costs 0.36 GSM8K — whether the weights retain latent
  reasoning under forced-CoT prompting is the open follow-up (pairs with the deferred
  exploratory lens probe). "Paying for justification buys the continued spending of inference
  tokens" — the constructive-complement framing, now with its control.

Lens probe (step 8): does NOT trigger — the prereg conditions it on P-DP-1 ∧ P-DP-3a passing
as confirmatory; 3a failed and the campaign is VOID.
