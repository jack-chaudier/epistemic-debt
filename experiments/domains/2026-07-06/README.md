# Tier 2 — domain battery (schema-generalization of the dissociation)

**Status: RUN COMPLETE (2026-07-06). PREREGISTERED — P-D3 (generalization) holds for gpt and
haiku; grok fails P-D3 on the frozen parser (3/4 applicable) but passes semantically (the one
failing cell is an abbreviation parser artifact). P-D2 splits hard: verdict survives for
gpt/haiku 6/6 but grok only 1/6.** See Verdict below.

Kills the schema-specificity fear: the within-item dissociation tested across **six
structurally distinct domains** (operations, clinical, software CI, loan underwriting, vendor
SLA, security triage) that share only the verdict interface. 600 items (100/domain, 50 DENIED).
Predictions fixed in `prereg_domains.md` (P-D1…D3). Scope: varies domain/surface, holds the
conjunctive/disjunctive logical structure constant (that sweep is a separate experiment).

## Files

- `items.jsonl` — 600 items, seeds 706020–706025, selfcheck clean (0 problems, all domains).
- `gen_items.py` — regenerates the corpus (deterministic; no LLM).
- `runner.py` — `run` / `smoke` / `score`; supports `--domain <key>` for per-domain runs.
- shared `../../lib/domains.py`, `../../lib/dissociation.py`.

## Run sequence

```bash
# 0. smoke — 3 items (first domain) end-to-end, INSPECT raw outputs first (~$0.02)
python3 runner.py smoke --model grok

# 1. full run — all 6 domains, three models (idempotent; --domain to shard/resume)
python3 runner.py run --model grok
python3 runner.py run --model haiku
python3 runner.py run --model gpt

# 2. score — per (model,domain) cells + P-D3 generalization verdict per model
python3 runner.py score
```

Reader = compressor, 15-word budget; hard cap 20,000 calls/model; est. < $4 total. Idempotent —
resumes from `responses_raw.jsonl`; a completed run re-scores for free.

## Domains

| key | register | verdict interface |
|---|---|---|
| ops_incident | operations go/no-go review | conjunction of 3 numeric thresholds; DENIED = 1 failing |
| clinical_enroll | trial screening chart | same |
| ci_release | software release gate | same |
| loan_underwrite | underwriting worksheet | same |
| vendor_sla | SLA scorecard | same |
| sec_triage | exposure triage sheet | same |

## Verdict

**Design recap.** 600 items = 6 structurally distinct domains × 100 (50 DENIED each), sharing
only the verdict interface (conjunction of 3 numeric thresholds; DENIED = exactly one failing).
Reader = compressor, contract-blind 15-word compaction, v5 protocol, corrected last-anchor
parser. Three models, variant 0. Applicability guard: a (model,domain) cell counts toward P-D3
only if fail-retention ∈ (0.15, 0.85) with n_lost ≥ 5 and n_kept ≥ 5. CIs are Wilson 95%.

**The dissociation generalizes across schemas.** P-D1 (which_lost CI-upper < which_retained
CI-lower AND which_lost.p < 0.34) per applicable cell:

| | ops | clinical | ci_release | loan | vendor | sec | P-D3 (prereg) |
|---|---|---|---|---|---|---|---|
| **gpt**   | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **holds 6/6** |
| **haiku** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | **holds 5/6** |
| **grok**  | ✅ | ❌* | ✅ | n/a | ✅ | n/a | **fails 3/4** (semantically 4/4*) |

`n/a` = inapplicable (retention outside the guard). grok's loan_underwrite (ret 0.90) and
sec_triage (ret 0.86) preserve almost every witness at 15 words → no populated lost cell.

**Per-prediction outcomes (prereg parser):**

- **P-D1 (dissociation)** — passes on **14 of 16** applicable (model,domain) cells (18 total; grok's loan and sec cells are inapplicable by the retention guard). The two
  non-passes are diagnosed below (one artifact, one honest elimination fail), not schema
  failures of the effect.
- **P-D2 (verdict survives, decision_lost ≥ 0.70)** — **gpt 6/6, haiku 6/6, grok 1/6**. This is
  the campaign's sharpest new result and is *not* about identification: grok's compressed
  summaries assert "all systems nominal" when the failing witness is dropped, and grok then
  **believes the gist and flips DENIED→APPROVED** (decision_lost 0.40–0.69 in five domains).
  gpt and haiku instead hold the verdict or abstain when the witness is missing. Note grok's
  no-notes prior is pure always-DENY (nonotes_deny = 1.00 everywhere), so its verdict loss is
  not prior-driven — the lossy artifact actively *overrides* a DENY prior with a false-nominal
  gist. The answer survives compaction for the panel, but for grok specifically it survives
  *worse* than its own blind prior would predict.
- **P-D3 (generalization)** — **gpt holds (6/6), haiku holds (5/6), grok fails on the frozen
  parser (3/4 applicable).** grok's single applicable fail is clinical_enroll, driven entirely
  by the abbreviation parser artifact below; under semantic scoring grok holds 4/4. Headline
  reported per the preregistered parser: **grok does not meet P-D3 as frozen.**

**Watch-items / audit notes.**

- **(a) Above-floor lost-cell identification = candidate-set elimination (budgetline confound
  #3), general across models.** Conditioning each lost cell on whether *all sibling* witnesses
  survive in the summary: P(name the failing parameter | all siblings kept) = 0.67–1.00 vs
  0.00–0.33 when any sibling is also lost. When every other candidate's value is present and
  passing, the model deduces the culprit is the one missing value — recovering identity without
  the witness, exactly the disclosed-candidate mechanism from budgetline. This is what pushes
  **haiku/sec_triage** which_lost to 0.444 (> 0.34) — an **honest P-D1 fail**, not a leak:
  sec_triage happens to drop the failing witness while keeping all siblings more often. Manually
  verified on all 8 haiku/sec_triage hits (e.g. "log coverage is not documented… PARAMETER: log
  coverage"). repair_param_correct_lost stays at/near the 1/3 floor for the low-retention cells
  and rises only where siblings survive — same mechanism, consistent story.
- **(b) Abbreviation parser artifact (disclosed, parser NOT modified).** `match_param`
  (preregistered, from runner3) prefix-matches *word tokens*; a single-token acronym the model
  writes in its own summary — LVEF, TG, SBP, CrCl, QTc, DTI, LTV, MTTR — matches no word of the
  multi-word canonical name ("left ventricular ejection fraction") and scores **UNMATCHED**.
  This hits only the **retained** cell (the model correctly identifies a surviving witness by
  its abbreviation), never the lost cell — so it is **strictly conservative for P-D1** (it
  *depresses* which_retained, shrinking the dissociation gap). Semantic-rescue sensitivity
  (mapping observed acronyms to canonical names; lost-cell numbers unchanged by construction):

  | cell | which_retained (prereg) | which_retained (semantic) | P-D1 flip |
  |---|---|---|---|
  | grok/clinical_enroll  | 0.333 | 1.000 | **fail → pass** |
  | grok/loan_underwrite  | 0.844 | 0.956 | (already n/a) |
  | gpt/clinical_enroll   | 0.714 | 1.000 | pass → pass |
  | haiku/clinical_enroll | 0.714 | 0.971 | pass → pass |
  | haiku/loan_underwrite | 0.919 | 1.000 | pass → pass |
  | haiku/sec_triage      | 0.906 | 0.938 | fail → fail (elimination, not this) |

  The **only** verdict this flips is grok/clinical_enroll, hence grok's frozen-parser P-D3 =
  fail vs semantic P-D3 = hold. This mirrors the 2026-07-06 last-anchor re-score (confound #2):
  a scoring regex, not model behavior, decides a headline verdict. Following the ground rule, the
  frozen parser is **not** edited mid-campaign; the artifact is disclosed here and the fix
  belongs in a separate re-score (the semantic-judge WHICH pass already planned for these raw
  responses). Anomaly counts surfaced, never binned: grok clinical 26 / loan 11 / sec 11 UNMATCHED
  (all acronyms); gpt ≤6 per domain; haiku clinical 12 UNMATCHED + 2 no-parse, loan 5+10, plus a
  handful of the prose-"parameter:" nested-anchor no-parses seen in Tier 1 (verbose refusals,
  semantically NONE/abstain, all in APPROVED or conservative positions).
- **(c) Realized compression length** (instructed 15 words): grok 22.5, gpt 21.8, haiku 23.5
  mean — all overshoot ~1.5×; retention differences across domains track witness density, not a
  model reliably hitting a shorter budget.

**Cost.** grok $0.27, gpt $0.51, haiku $4.05 — **$4.83 total** (10,800 calls; cache made every
crash-resume free).

**Interpretation.** The schema-specificity fear is largely dead: the identification/verdict
dissociation reproduces in 14 of 16 applicable cells (15/16 under semantic scoring) across six unrelated document registers,
with the two exceptions fully explained (one scoring artifact, one honest elimination effect
predicted by the disclosed candidate-set confound). What got stronger: the effect is a property
of lossy compaction, not of the incident schema. What got *weaker and more interesting*: P-D2
reveals that "the verdict survives" is model-specific under domain stress — grok trusts a
false-nominal gist and loses the verdict in 5/6 domains despite an always-DENY prior, while
gpt/haiku hold it everywhere. The bias-shelf reading (answer = prior, not knowledge) does not
even save grok here: its prior would say DENY, its gist-belief says APPROVE, and the gist wins.
The single highest-value follow-up is the semantic-judge WHICH re-score over these cached
responses, which would both retire the abbreviation artifact and let elimination-vs-retrieval
be measured directly per domain.
