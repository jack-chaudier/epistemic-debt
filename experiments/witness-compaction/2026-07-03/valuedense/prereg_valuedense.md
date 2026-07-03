# Phase A preregistration — can a contract-blind compactor pay for witnesses it doesn't know it needs?

Fixed 2026-07-03, before any Phase A API call.

## Question

The manifest experiment showed *declaring* loss doesn't help. This phase tests whether changing the **compaction objective** does — still fully contract-blind (the compactor never sees the policy). Theory framing: with 12 candidate witnesses (parameter readings) of which 3 are secretly decision-relevant, a 15-word budget holds at most ~4–5 name+value pairs; a blind compactor cannot beat the covering bound (expected policy retention ≈ values-kept/12 if selection is uninformed), but plain-prose compactors don't even reach it (v5 grok baseline retention 0.344 with much of the budget spent on prose). The achievable frontier under blindness sits between the prose baseline and the contract-aware ceiling (≈0.97, pilot v1). Where?

## Design

v5 corpus (60 items), 15-word budget, models **grok** and **haiku** (baselines: their v5 plain-15 runs). Two new arms, both contract-blind:

- **valuedense**: same compaction prompt + "Prefer concrete parameter readings (name, number, unit) over prose; keep the readings most likely to decide any pass/fail or threshold question."
- **auditor** (two-pass): pass 1 — "List the 6 facts from this file a future auditor would most need" (blind); pass 2 — compress to 15 words using that list. Both passes count in cost; the *artifact* budget is the same 15 words.

Probes per arm: DECISION, WHICH, WHICH-ABSTAIN from the arm's own summary. Cells by failing-value retention as usual. Calls: ≤ 60×4 (valuedense) + 60×5 (auditor) per model ≈ 1,080 total; hard cap 1,500.

**Amendment (2026-07-03, after 3-item smoke, before any confirmatory scoring):** the value-dense objective causes budget overshoot (grok realized 28–39 words vs instructed 15, even with "hard limit" phrasing; the auditor arm complies at 11–18). Realized-length inflation is the documented metric confound, so each arm is evaluated against a **realized-length-matched plain control**: valuedense (realized ≈ 33w) compares against the cached manifest-phase `plain25` arm (grok realized 33.6w, haiku 34.4w); auditor (realized ≈ 15w) compares against the v5 `plain15` baseline (grok 19.1w, haiku 21.0w). Prompt-noncompliance under a witness objective is itself recorded as an exploratory finding. Prediction thresholds unchanged; only the comparison baseline per arm is fixed as above. Smoke records preserved in `smoke_v1_responses.jsonl` (prompt v1, discarded from scoring).

## Preregistered predictions (per model per arm vs that model's realized-length-matched plain control)

Baselines (from v5_results.json): grok retention 0.344, WHICH-overall-DENIED 8/30 ≈ 0.267 pass-through… computed identically for arms; haiku retention 0.339, WHICH-overall-DENIED 11/30 ≈ 0.367.

- **P-A1 (the objective buys witnesses)**: mean policy retention ≥ baseline + 0.15.
- **P-A2 (witnesses buy justification)**: WHICH accuracy over all DENIED items ≥ baseline + 0.15. (Unconditioned on cells, so it can't be gamed by cell migration; this is the "justified accuracy rises at equal budget" test.)
- **P-A3 (blindness still has a price)**: mean policy retention ≤ 0.80 — the blind frontier stays below the contract-aware ceiling. A *failure* of A3 (blind retention > 0.80) would be the stronger headline: near-free witness preservation without knowing the query.
- **P-A4 (the shelf persists wherever loss persists)**: within each arm, WHICH-lost ≤ 1/3 and WHICH-retained ≥ 0.7 (applicability n≥8 per cell) — i.e., the intervention moves items *between* cells; it does not rescue items whose witness is still destroyed.

Campaign criterion: a prediction generalizes if it passes in ≥3 of the 4 (model × arm) combinations.

## Exploratory

Realized word counts (budget compliance); value count per summary; which parameters get kept (selection-vs-chance); decision accuracy shifts; abstention calibration; auditor pass-1 list quality.

## Budget

≤ 1,500 calls this phase; cost reported cumulatively.
