# Forced-CoT probe on Student-V (+ exploratory lens) — 2026-07-09

**Prereg frozen at 8b94ffb before spend. One RTX 4090 pod (tu7ibwiu9kmv49), 03:09–03:55 UTC
≈ 0.78h × $0.69 ≈ $0.54. $0 API. 4,740 behavioral calls + 180 lens forward passes. Pod
deleted; account at zero.**

## Verdict

- **P-FC-0 PASS** (compliance): V emits real reasoning under forced-CoT (GSM8K median 205
  completion tokens; the smoke shows genuine stepwise arithmetic).
- **P-FC-1: LATENT — the keystone.** Student-V forced-CoT GSM8K **0.448** (bare 0.152;
  latent threshold 0.387). Verdict-only SFT trained *silence*, not damage — the reasoning
  machinery survives and can be re-elicited by prompt. **The silent-CoT paper is
  "audit your evals," not "the recipe destroys models."**
- **Upset #1 — forced-CoT is NOT neutral instrumentation:** under the SAME forced-CoT prompt,
  base drops 0.516 → 0.324 and Student-J **crashes 0.524 → 0.204**. Each model reasons well
  only in its trained/natural register; V under forced scaffolding *beats base* under forced
  scaffolding. Any eval that standardizes a CoT prompt is measuring register match, not
  capability. (Also decisive for the parity redesign: register-forcing moves every model
  differently, so eval-time prompting cannot engineer parity.)
- **P-FC-2 FAIL — the section is not prompt-overridable:** V's fail-open approve rate barely
  moves under evidence-checking CoT (0.997 → 0.953; J 0.918 → 0.890). The smoke shows *why*:
  asked to quote readings from the ablated file, V **confabulates readings that don't exist**
  and then approves — the drift generates its own evidence. Meanwhile base FLIPS under CoT
  (0.814 → 0.260, fail-open → fail-closed): the section has a *register* index on top of the
  (model × mutilation-type) indexing from the sections campaign.
- **P-FC-3 split:** sv half PASS (abstains 0.000 with the out offered — the fail-open section
  ignores it, as predicted); sj half FAIL (abstains only 0.092 on surgical ablation, vs its
  0.76 hedge share on no-notes probes — the [MISSING DATA] register does NOT generalize to
  clean-looking wounded documents).
- Base Qwen3-1.7B is itself fail-open under surgical ablation (abl_bare approve 0.814,
  grok-like closed-world reading) — Student-V's 0.997 is the base tendency amplified to
  ceiling, not created from nothing.

## Lens probe (EXPLORATORY)

On 60 of V's fail-open cells, per-layer (APPROVED − DENIED) logit-lens gaps at the answer
position: **computed-but-outvoted** (a second-half layer prefers DENIED before the final
approve) in 16/60 for V, 31/60 for base, 0/60 for J; never-computed (no DENIED-preferring
layer anywhere) 0/60 everywhere. Reading: the deny/insufficiency signal survives mid-stack in
a quarter of V's fail-open decisions and is outvoted late — V-training didn't erase the
computation, it re-weighted the last layers; J's approve decisions are approve-dominant
through the whole second half. Caveats: second-half threshold is stated-but-arbitrary; a PEFT
adapter-reload warning fired before the sj pass (contamination risk noted); exploratory label
per prereg.

## Files

`prereg_forced_cot.md` (frozen), `runner_fc.py`, `lens_probe.py`, `score_fc.py`,
`sections_items.jsonl` + `capability_items.jsonl` (frozen corpora, copied), raw responses,
`forced_cot_results.json`, `lens_results.json`. One scorer bug fixed post-hoc and disclosed
(`0.0 or 1` truthiness swallowed sv's legitimate 0.000 abstain; P-FC-3 sv half corrected to
PASS).
