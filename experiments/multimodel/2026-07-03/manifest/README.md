# manifest — loss-manifest compaction intervention

Design and predictions: [prereg_manifest.md](prereg_manifest.md). Equal-instructed-budget arms: plain-25-words vs 15-word notes + one `OMITTED:` line (≤10 words), both contract-blind, on the v5 corpus; grok/haiku/gpt (gemini quota-infeasible).

Verdict: **P-M1 (fabrication drops ≥30 pts) FAILS the campaign criterion** — passes only haiku (0.94→0.54); grok and gpt fabricate repairs at 1.00 in both arms. **P-M2 (verdict unharmed) passes 2/3** (fails grok, with a confound: grok overshot the plain-25 instruction to 33.6 realized words vs 24.5 in the manifest arm, so the arms weren't realized-budget-matched for grok). Robust side effect: abstention uptake rises on all three models (0.60→0.78, 0.63→0.92, 0.61→1.00).

Interpretation (Appendix F.5): a loss ledger buys calibrated abstention for free but cannot bolt honesty onto the action channel — the prompt-level recurrence of the retrofit gap.
