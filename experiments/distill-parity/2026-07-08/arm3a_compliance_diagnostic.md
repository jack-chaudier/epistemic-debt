# Arm 3a compliance diagnostic (frozen on commit, BEFORE any eval data exists)

Lead directive 2026-07-08, pre-committed so the interpretation is decided before we see which
way it cuts. Context: the r1 register makes the J condition unambiguous short-CoT distillation —
the teacher's own DENIED accuracy moves 0.427 → 1.000 across verdict/evidence orderings, so the
pre-verdict tokens demonstrably carry computation. At eval, the frozen format-neutral Arm 3a
probe requests a bare ANSWER line; Student-J may emit its trained evidence-first register
anyway. Then an Arm 3a V−J gap could be partly *inference-time* token computation rather than
purely weight-borne. The frozen scoring stands unchanged; this is a secondary analysis.

## Definitions (mechanical)

- **Decision parse (all models, all arms):** last `ANSWER:` anchor (colon required); fallback
  last bare APPROVED/DENIED token. Last-anchor per confound-checklist #2.
- **Bare-compliant trial:** the response, whitespace-stripped, is exactly one line matching
  `^ANSWER:\s*(APPROVED|DENIED)\.?$` (case-insensitive). Anything else = **preamble trial**.
- **Reported per model on Arm 3a:** bare-compliance rate; accuracy split into bare-only vs
  preamble trials (with Wilson CIs and cell sizes; cells under n=20 reported but flagged
  underpowered).

## Interpretation rule (decided now)

1. If the V−J error gap (P-DP-3a direction) **survives on bare-only trials** with CI
   separation, the weight-borne reading is airtight: the justification-trained weights decide
   better even when no justification tokens are emitted.
2. If the gap **lives entirely in preamble trials** (bare-only gap ≈ 0), the honest headline
   becomes: *paying for justification in training buys reasoning the model spends at
   inference* — Law 1's constructive complement, mechanism named. P-DP-3a's frozen pass/fail
   is still reported against its threshold as written; this diagnostic labels the mechanism,
   it does not rescue or demote the prediction.
3. Mixed case (gap attenuated but nonzero on bare-only): report both numbers, headline claims
   only the bare-only magnitude as weight-borne.

Symmetric numbers for Student-V are reported as the control (its trained register IS the bare
line, so its compliance is expected ≈ 1.0 — a V compliance drop would itself be an anomaly to
surface).
