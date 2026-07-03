# v5 — multi-model preregistered replication (+ calibrated-prior criterion)

Design and predictions: [prereg.md](prereg.md) (fixed before any call; two dated amendments re the free-tier Gemini key). Fresh 60-item corpus (seed 5151), 15-word contract-blind compression, 6 calls/item/model.

Verdict: P-A5/P-B/P-C/P-D **pass on both applicable models** (grok, haiku — WHICH-lost 0/22 and 0/19). P-E split (pass grok 0.624 vs 0.500; fail haiku 0.574 vs 0.487) — the bias-shelf reading survives. P-F fails on haiku (1/19): incoherence is a model-specific phenotype. gpt-4.1-mini inapplicable at 15 words (retention 0.100 — it spontaneously implements the bare answer quotient); exploratory 30-word arm (`explore_wide30.py`, `wide30_results.json`) shows the full pattern. Confounds found: realized summary length varies by model (covariate, within-model cells unaffected); gemini arm quota-infeasible.

Full interpretation: theory doc Appendix F; campaign overview one directory up.
