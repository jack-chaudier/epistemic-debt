# Phase C preregistration — does epistemic debt compound under recursive compaction?

Fixed 2026-07-03, before any Phase C API call.

## Question

Real long-context systems don't compress once — they re-compact rolling summaries. Two hypotheses: (i) **compounding** — each generation re-decides what to keep with no memory of what mattered, so witness survival decays multiplicatively and gist itself corrupts (telephone effect); (ii) **near-idempotence** — the first compression does all the damage, and re-compacting a summary is close to lossless because the summary is already value-dense. Which regime LLM compaction sits in determines whether "infinite context via rolling compaction" silently accumulates debt or just pays a one-time toll.

## Design

Model: grok. Items: the 30 DENIED v5 items. Two arms:

- **direct**: document → 15 words (one compression; reuse of the phase-B 15w cache is permitted since the prompt/model/items are identical — noted for provenance).
- **chain**: document → 80 → 40 → 15 words. Each step sees *only* the previous step's notes ("case notes" framing, same contract-blind wording), never the document.

Probes at the final 15-word artifact for both arms: DECISION, WHICH. Intermediate chain artifacts also scored for retention (no probes) to trace the decay path. ≤ 350 calls; hard cap 500.

## Preregistered predictions

- **P-C1 (data-processing sanity)**: chain final policy retention ≤ direct retention + 0.05. (A violation would mean the matcher or design is broken, not physics.)
- **P-C2 (compounding, the real bet)**: chain final retention ≤ direct retention − 0.10 — the chain loses strictly more witnesses than one-shot compression to the same budget.
- **P-C3 (gist corrupts too)**: chain DECISION accuracy ≤ direct DECISION accuracy − 0.10.

Interpretation fixed in advance: C2∧C3 pass ⇒ rolling compaction is a debt *multiplier* (infinite context accumulates silent debt with generation depth — the negative result for naive rolling-summary architectures). C2∧C3 both fail ⇒ compaction is near-idempotent: debt is set by the final budget, not the path (the good-news null: rolling compaction costs little beyond the one-time toll). A split is reported as-is.

## Exploratory

Retention at each generation (80w, 40w, 15w) vs the matched direct budgets from phase B (same budgets, same items) — the per-generation decay factor; failing-value hazard by generation; WHICH accuracy on the chain.

## Budget

≤ 500 calls, grok only.
