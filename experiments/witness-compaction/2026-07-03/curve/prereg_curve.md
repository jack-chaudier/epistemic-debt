# Phase B preregistration — the exchange rate as a curve

Fixed 2026-07-03, before any Phase B API call.

## Question

The shelf has so far been measured at single budgets. Sweep the compression budget and trace the answer channel and the reason channel as *curves*: does the gap between them open sharply (a shelf edge / phase-transition-like knee) or gradually? The Shelf Width Law's finite-model reading predicts an *interval* of budgets where answers are saturated and witnesses are not; its LLM shadow is the horizontal distance between the two curves' rise points.

## Design

Model: grok-4-1-fast-non-reasoning. Items: the 30 DENIED items of the v5 corpus. Budgets: **{5, 10, 15, 25, 40, 60, 80} words**, plain contract-blind compaction prompt (v5 wording, budget substituted). Per budget per item: COMPRESS, DECISION, WHICH = 630 calls; hard cap 800. Metrics per budget: mean policy retention, failing-value retention rate, DECISION accuracy, WHICH accuracy (all unconditioned on cells — cell sizes shift with budget by design).

## Preregistered predictions

- **P-B1 (the answer channel saturates immediately)**: DECISION accuracy on DENIED ≥ 0.75 at **every** budget including 5 words. (The verdict rides on prior+gist; it needs almost no budget.)
- **P-B2 (the reason channel is budget-bound and monotone)**: WHICH accuracy is non-decreasing in budget up to noise — no drop > 0.10 between consecutive budgets — and spans the range: WHICH(5w) ≤ 0.2, WHICH(80w) ≥ 0.8.
- **P-B3 (a wide shelf interval exists)**: the set of budgets where DECISION ≥ 0.75 AND WHICH ≤ 0.5 spans at least {5, 10, 15} (i.e., the shelf is at least ~3× wide in budget terms at the low end).

## Exploratory (labeled)

Logistic fit of WHICH vs realized (not instructed) word count — midpoint and slope; retention-vs-budget linearity; where failing-value survival crosses 0.5; comparison of the WHICH curve with the retention curve (does justification track retention 1:1, i.e., is the reader a pass-through of the artifact?).

## Budget

≤ 800 calls, grok only.
