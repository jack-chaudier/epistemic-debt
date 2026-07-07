# Tier 2 preregistration — domain battery (schema-generalization of the dissociation)

Fixed 2026-07-06, before any API call. Corpus `items.jsonl` (600 items = 6 domains × 100,
seeds 706020–706025) generated and confound-checked (clean, 0 problems) before finalization.

## Purpose

Kill the **schema-specificity** fear. Every prior shelf result used the incident corpus (plus
one clinical variant). If the within-item dissociation replicates across six *structurally
distinct* document registers, the shelf is not an artifact of the incident item schema.

The six domains share only the **verdict interface** (a conjunction of three numeric-threshold
criteria; APPROVED iff all hold; DENIED = exactly one failing), so the scoring machinery is
constant. Everything else differs — parameter names/units, document register, event framing:

| domain | register | example parameters |
|---|---|---|
| ops_incident | operations go/no-go | ullage pressure, gyro drift, telemetry margin |
| clinical_enroll | trial screening chart | neutrophil count, ejection fraction, QT interval |
| ci_release | software release gate | test pass rate, p95 latency, error budget |
| loan_underwrite | underwriting worksheet | credit score, DTI, loan-to-value |
| vendor_sla | SLA scorecard | uptime, resolution time, defect escape rate |
| sec_triage | exposure triage sheet | CVSS, patch age, blast radius |

**Scope note (what this does and does not test).** This varies domain/surface while holding the
*logical* structure fixed (conjunctive policy, disjunctive DENIED). It is a domain-generalization
test, not a policy-structure test — the conjunctive/disjunctive coarseness sweep (theory Appendix
C / roadmap item 2) is a separate experiment. Stated here so the claim is not over-read.

## Design

Reader = compressor, contract-blind 15-word compaction, the standard protocol (compress →
decision, which, which_abstain, repair, nonotes), corrected parser. Three models
(grok-4-1-fast, claude-haiku-4-5, gpt-4.1-mini). n = 50 DENIED per domain → lost/retained cells
comparable to or larger than the v4/v5 originals, per domain.

## Preregistered predictions (per model × domain, Wilson 95% CIs)

- **P-D1 (dissociation, per applicable cell)**: `which_lost` CI upper < `which_retained` CI
  lower AND `which_lost.p` < 0.34. *Primary.*
- **P-D2 (verdict survives)**: `decision_lost.p` ≥ 0.70.
- **P-D3 (generalization)**: for each model, P-D1 holds on ≥ 5 of 6 domains, counting only
  **applicable** cells (fail_retention ∈ (0.15, 0.85) and n_lost ≥ 5 and n_kept ≥ 5 — the v5
  guard: a model that collapses to pure gist or preserves everything at 15 words has no
  populated split and is not counted, with its retention reported).

Campaign reading: P-D3 per model is the headline generalization claim. Domains where a model's
retention falls outside (0.15, 0.85) are reported as inapplicable (not failures) with their
retention, since the shelf is only measurable where witnesses are actually sometimes destroyed.

## Budget

3 models × 600 items × 6 calls = 10,800 calls. Hard cap 20,000/model. Estimated < $4.
Idempotent — re-running is a no-op; per-domain and per-model runs resume from cache.
