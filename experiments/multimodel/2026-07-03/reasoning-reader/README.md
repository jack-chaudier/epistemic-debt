# reasoning-reader — can inference-time compute buy back artifact-borne debt?

Design and predictions: [prereg_reasoning.md](prereg_reasoning.md). Answerer: **gpt-5-mini** (reasoning tier, default effort; the API fixes temperature=1 — single cached run, determinism caveat noted). Artifacts: grok's cached v5 summaries (22 lost / 8 retained DENIED). 180 calls.

Verdict: **all three predictions PASS.** which-lost 4/22 (0.182, CI [0.073, 0.385] — below the 1/3 guessing bar), which-retained **8/8**, abstain 20/22 vs 0/8, decision-lost 0.909. A reasoning model reading a witness-free artifact does not recover the witness: **inference-time compute is not a substitute for witness bits.** Context-engineering consequence: paying for a smarter reader cannot repair a cheap compactor — the debt is set upstream, at compaction. Exploratory: gpt-5-mini's incoherence-on-lost is 0.27 (between haiku's ~0 and grok/gpt's ~0.7) and confabulated-WHICH 0.136; reasoning cost ≈ $0.19 for 180 probes.
