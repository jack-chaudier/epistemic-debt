# NEXT — live scratchpad: next steps, open questions, ideas

Agent- and human-facing. Read this before proposing new work; append to it when a run or a
re-analysis surfaces something worth chasing. Conventions:

- **Queue entries** carry: what / why (which fear or law it addresses) / design sketch / est.
  cost / status. Move an entry to *done* (with the artifact link) rather than deleting it.
- **Ideas** are cheap to add and carry no obligation — date them, one paragraph max.
- This file is a map, not a ledger. Claims live in `results/RESULTS.md` with evidence labels;
  nothing here is citable. Preregister before spending (see CLAUDE.md).
- Current shared infrastructure for new campaigns: `experiments/lib/domains.py` (6
  confound-guarded generators + mechanical selfcheck) and `experiments/lib/dissociation.py`
  (protocol, corrected parser, Wilson CIs, idempotent cache). Copy the highpower/domains
  campaign shape: `gen_items.py` + `prereg_*.md` + `runner.py` (smoke/run/score) + README
  verdict + a regression test pinning the headline numbers.

## Queue (ranked by leverage per dollar)

1. **Semantic-judge WHICH re-score of the Tier 1+2 cached responses.** (~$0.50, no new
   compression calls.) Retires the abbreviation parser artifact that decided grok's P-D3
   (LVEF/SBP acronyms → UNMATCHED — third scoring-regex incident), applies the
   NONE_NO_FAILURE / NONE_MISSING_DATA split at scale (n≈900 lost-cell responses vs the
   original 19–28), and measures elimination-vs-retrieval per domain directly. Pattern exists:
   `experiments/rescore/2026-07-06/judge.py` (dual judge, adjudication file, agreement bar).
   Status: **ready to build**.
2. **Gist-belief follow-up (the P-D2 discovery).** Why does grok trust its own false-nominal
   gist over its always-DENY prior while gpt/haiku hold the verdict? Design: same corpora,
   probe the *decision* channel with (a) summaries stripped of gist adjectives ("nominal",
   "no issues"), (b) gist-only summaries (no values), (c) the manifest `OMITTED:` line —
   isolate whether the flip is driven by asserted-normality tokens. This is a new failure
   mode (compaction manufacturing a wrong answer with a reassuring gist); it deserves its own
   named result. (~$3.) Status: design sketch only.
3. **Fresh preregistered loss-ledger router run.** The row-21 result (recall 1.00, 30/30) is
   OBSERVED on cached data with a simulated ledger. Real version: compactor emits dropped
   value-*names* out-of-band; router intersects ledger with the query's policy; include a
   debt-rare corpus arm for the token-economics story P-D3(routing) left open. (~$3.)
   Status: mechanism validated, needs the honest run.
4. **Law 3 / distillation kill-shot — the headline gap.** Teacher–student ladders that exist
   in the market (gpt-4.1→mini→nano; gemini flash→flash-lite; sonnet→haiku): match on standard
   items, diverge on counterfactual re-queries; prediction: witness fidelity falls before
   accuracy, students degrade disproportionately. The economically central law has zero
   experiments. (~$10–20.) Status: unstarted; biggest strategic hole.
5. **Real-document tier (external validity — the last big fear).** Semi-synthetic injection:
   real transcripts/PR threads/postmortems with decision-relevant values planted in natural
   prose (controlled ground truth, real linguistic texture). Also the in-harness variant:
   probe an actual Claude Code session's post-compaction agent against the pre-compaction
   transcript. Status: unstarted; gates any external claim about production systems.
6. **Honesty Theorem exact check.** ($0 — pure computation.) The vendored frontier machinery
   can decide whether calibrated abstention requires the full witness quotient or a cheaper
   intermediate state exists; either outcome is a result (a new quotient between M and Q).
   Status: machinery in `proofs/vendor/exact_pareto_frontier.py`, unwired.
7. **Coarseness sweep, conjunctive/disjunctive (roadmap item 2).** Shelf ∝ answer-quotient
   coarseness — the remaining quantitative theory test; Tier 2 deliberately held logical
   structure fixed, this varies it. (~$3.)
8. **Small cheap ones:** compaction-path ensembles (chain∪direct witness union was 14/30 vs
   10–11 alone — is diversity a real intervention? ~$1); the U-shaped decision curve (verdict
   accuracy worst at mid-compression — characterize the dip, possible standalone note);
   Gemini P-G3 completion when a billed key exists.

## Open theory questions

- **Formalize J = α·S + β.** Reader efficiency α is model-specific (0.89–1.20 corrected);
  α>1 = candidate-set elimination (disclosed-candidate recovery), α<1 = retrieval slippage.
  What determines α? Is it stable per model across corpora? (Tier 1+2 data can answer the
  stability question for free.)
- **The gist channel as a second information carrier.** P-D2 shows the artifact carries not
  just values but *asserted normality*, and some readers weight it above their prior. The
  quotient theory has no slot for this — the summary's rhetorical stance is neither answer
  nor witness. Candidate formalization: gist = a noisy verdict token embedded in the artifact.
- **Blind-vs-aware covering gap** (Appendix H.5): blind compactor pays Σ|candidates|, aware
  pays fiber entropy; price of blindness → 0 when candidates fit the budget. Prove it.
- **Fibered Shelf Width Law + repositioning** on Myhill–Nerode / ε-machines / Vorob'ev before
  any external claim (risk-register item; unchanged).

## Ideas parking lot (dated, no obligation)

- 2026-07-06 — *Coherent-debt-acknowledgment rate as a training metric.* Haiku natively says
  "the readings are absent" (0.79) where grok/gpt assert contradictions (0.00). If that rate
  were tracked during model training the honesty premium says it's cheap to buy there and
  ~38× to retrofit. Possible short position paper: "measure debt-acknowledgment, not
  hallucination."
- 2026-07-06 — *Unparseable output as a debt signal.* Format degradation concentrates on
  lost-witness items (retained cells parse perfectly). A production system could treat
  parse-failure rate as a free debt proxy. Worth one exploratory plot over existing data.
- 2026-07-06 — *Realized-vs-instructed budget as the control knob.* The paraphrase arm halved
  realized length at the same nominal budget; every campaign shows overshoot ~1.5×. Compaction
  contracts should be specified in realized tokens, not instructed words — engineering note
  for the ledger-router design.
- 2026-07-06 — *Startup framing (from the market scan):* the durable asset is deterministic,
  judge-free debt measurement (ledger = guaranteed floor, not accuracy estimate — J ≥ S is the
  honest fine print), wedged into regulated voice agents; Morph/platform compaction absorbs
  the "preserve values" half. Kill-risk: table-stakes absorption. Fallback: own "justified
  accuracy" as an open standard.

## Done (moved from queue)

- ~~High-power replication (Tier 1)~~ → `experiments/highpower/2026-07-06/` — P-H1/H2/H4 3/3,
  P-H3 2/3 (haiku over-abstains); prior objection retired for haiku/gpt.
- ~~Domain battery (Tier 2)~~ → `experiments/domains/2026-07-06/` — P-D1 14/16 applicable
  (15/16 semantic); NEW: P-D2 gist-belief-overrides-prior split (grok 1/6 vs gpt/haiku 6/6).
- ~~Parser-artifact audit + phenotype re-score~~ → `experiments/rescore/2026-07-06/`.
- ~~J = S budget line~~ → REFUTED toward J ≥ S, `experiments/laws/2026-07-03/budgetline/`.
- ~~Honesty premium reproduction~~ → `proofs/honesty_premium.py` (0.47×, 38.4×, dichotomy).
