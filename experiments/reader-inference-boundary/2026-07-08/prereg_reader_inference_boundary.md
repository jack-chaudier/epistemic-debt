# Preregistration — Reader inference boundary (what depth of read-time recovery is real?)

Fixed 2026-07-08, **before any API call**. Corpus `items.jsonl` is generated and
confound-checked (mechanical `selfcheck`, 0 problems) before finalization. Candidates are
**DISCLOSED** in every probe (see "Candidate-set disclosure" below) — this run measures
*deployed* read-time reasoning, not hidden-artifact content.

## The contradiction this resolves

The repo holds two results that point opposite ways about how much *inference* a reader does
when it names the justification for a surviving answer:

- **Appendix G.2 (retrieval, not inference):** on p=1 items the verdict logically forces the
  reason, yet grok names it only 2/13 when the value is dropped — "the model treats *name the
  reason* as retrieval of the value from context, not as inference from verdict + policy
  structure." Readers do *less* than logical inference.
- **Appendix I.3 / budgetline (elimination beyond survival):** J ≥ S because readers recover
  the failing parameter by **elimination over the disclosed candidate set** — reader efficiency
  α up to 1.20. Readers do *more* than string retrieval.

Both can be true if read-time recovery is exactly a **shallow, fixed-depth** operation:
identity-elimination over the disclosed candidate set (including the trivial "name the one whose
value is missing"), but **not** numeric evaluation. This experiment measures where that boundary
sits, and whether it is the same across models — i.e. whether **read-time inference depth is a
measurable constant of behavior-optimized readers** (the 2026-07-07 idea in NEXT).

## Design — a pure read-channel probe (no compressor)

Unlike every prior campaign, **there is no compaction call**. The "compressed case notes" are
*constructed deterministically* so that derivability is controlled exactly, not left to what a
live compressor happened to drop. This removes the compressor confound and lets us set the
required inference depth precisely. Reader input per probe = `policy_text` (discloses the three
candidate parameter names) + constructed `notes` + one question.

Every item: a 3-condition conjunctive policy (APPROVED iff all three numeric thresholds hold),
ground truth **DENIED with exactly one failing policy parameter (the culprit)**. The four classes
differ *only* in how the notes encode the three policy readings, hence in the read-channel
operation needed to name the culprit:

| class | notes encode… | culprit nameable by | no-inference baseline |
|---|---|---|---|
| **(a) UNDERIVABLE** | none of the 3 policy values (distractors only) | nothing — guess over 3 disclosed candidates | ~1/3 |
| **(b) ELIM / absence-spotting** | the 2 non-culprit values, plainly, both passing; culprit value omitted | "name the candidate whose value is missing" / eliminate the 2 present passers | ~1/3 (guess) |
| **(c) ARITHMETIC** | 1 non-culprit value plainly (passing); the culprit AND the other non-culprit each given only as a one-step arithmetic expression (`base ± offset`), culprit resolving to a fail, the other to a pass | eliminate the 1 plain passer, then **compute** the two expressions to see which fails | ~1/2 (guess between the 2 expression-encoded candidates) |
| **(d) RETRIEVAL (positive control)** | culprit value plainly present and failing; the 2 non-culprits plainly present and passing | read the failing value directly | n/a (should be ~1.0) |

Key design choices that defeat cheap heuristics:

- In **(c)**, nothing is absent (all three parameters are mentioned) so the "absent = culprit"
  heuristic that solves (b) does not apply; and two candidates are expression-encoded so
  "verdict + one plain passer ⇒ the other fails" does not isolate a single candidate. The
  culprit is identifiable *only* by performing at least one arithmetic evaluation. This matches
  the queue's "(c): two elimination steps or one arithmetic step."
- Arithmetic in (c) is a single integer addition/subtraction with a comfortable pass/fail margin
  (`selfcheck` enforces integer `base`/`offset` and margin ≥ 15% of threshold, so a *correct*
  computation is unambiguous). This tests whether ONE trivial arithmetic step is *deployed at
  read time*, not arithmetic capacity — the capacity control (P-RIB-5) settles that separately.

Probes per item (exact-format, last-anchor parser reused from `dissociation.py`):
1. **WHICH** (primary): `PARAMETER: <name>` or `PARAMETER: NONE`.
2. **WHICH-ABSTAIN** (secondary): WHICH + explicit `PARAMETER: INSUFFICIENT_EVIDENCE` option —
   separates honest abstention from confabulation in (c).
3. **DIRECT-ARITH** (capacity control, (c) items only): the item's arithmetic in isolation
   ("A reading was `offset` `unit` higher than `base` `unit`; is it at least `T`? Reply
   PASS/FAIL"), to prove the model *can* do the computation on demand.

Models: `grok` (grok-4-1-fast-non-reasoning), `haiku` (claude-haiku-4-5), `gpt` (gpt-4.1-mini),
temperature 0, idempotent cache keyed by (model, item, call), hard cap 3000/model.

Corpus: N = 60 items per class × 4 classes = 240 items, balanced across the 6 `domains.py`
registers, seeds fixed in `gen_items.py`. Recovery = `parse_which → match_param == culprit`;
`NONE`/`INSUFFICIENT`/`UNMATCHED` count as non-recovery and are surfaced separately (never
silently binned — the 2026-07-06 parser-artifact rule).

## Preregistered predictions (per model; Wilson 95% CIs; recovery on the WHICH probe)

- **P-RIB-0 (retrieval control):** `recovery(d) ≥ 0.85`. *Sanity — the WHICH channel works; a low
  (c) is then specifically about arithmetic, not a broken probe.*
- **P-RIB-1 (elimination/absence-spotting works):** `recovery(b) ≥ 0.75`. *Replicates the
  budgetline elimination mechanism as a controlled manipulation.*
- **P-RIB-2 (arithmetic recovery fails — the G.2-extension):** `recovery(c) ≤ 0.50`.
- **P-RIB-3 (the depth boundary is real):** `recovery(b) − recovery(c) ≥ 0.25` AND Wilson CIs
  separated (`b.ci_lower > c.ci_upper`).
- **P-RIB-4 (elimination is genuine, not prior):** `recovery(a) ≤ 0.50` AND `b.ci_lower > a.ci_upper`.
- **P-RIB-5 (arithmetic is within capacity):** DIRECT-ARITH accuracy `≥ 0.85`. *If P-RIB-5 passes
  while P-RIB-2 passes, the (c) failure is a **deployment** boundary, not a capacity limit — the
  strong claim.*

### Verdict logic (stated before the run)

- **Boundary confirmed (headline A):** if, on **all 3 models**, P-RIB-0/1/2/3/5 pass, then
  read-time recovery is depth-1 identity-elimination but **not** numeric evaluation, and the
  boundary is a cross-model constant. This is a **new PREREGISTERED law** sharpening G.2 / Law 1:
  compression sheds the witness AND the read channel cannot recompute it past elimination depth,
  *even when the arithmetic is one trivial step within the model's demonstrated capacity*.
- **Retrieval reading refuted (headline B, equally publishable):** if P-RIB-2 fails (recovery(c)
  high) on ≥1 model with P-RIB-5 passing, readers **do** deploy arithmetic recovery — the G.2
  "retrieval-not-inference" reading is wrong, and α's ceiling is higher than elimination.
- **Split:** report per model; a model-dependent boundary is the α-heterogeneity story (I.3),
  reported as OBSERVED, not a universal constant.

Any other combination is reported prediction-by-prediction; no post-hoc relabeling.

## Confound checklist (CLAUDE.md, decided per-run)

1. **Salience / verdict leak:** notes contain no APPROVED/DENIED/pass/fail/spec/threshold/
   out-of-range language (`selfcheck` runs the `domains.py` `VERDICT_WORDS` guard over the notes).
   The *offset direction* words ("higher/lower than") describe a prior reading, not spec status.
2. **Last-anchor parsing:** WHICH parsed by the corrected last-`PARAMETER:` (colon-required)
   parser; `UNMATCHED` counts surfaced in the results JSON per cell.
3. **Candidate-set disclosure — DISCLOSED (stated):** `policy_text` names all three candidates in
   every probe. This is deliberate: the experiment measures *deployed* recovery over a disclosed
   set (the I.3 "deployed J" quantity), and depth is only meaningful when the candidate set is
   known. A candidate-hidden variant would measure artifact content and is a separate future run.
4. **Ground-truth / arithmetic correctness (`selfcheck`):** exactly one failing policy param;
   `match_param(culprit) == culprit`; every disclosed number pairwise non-colliding under
   `retained()`; in (c) `base ± offset` equals the intended value, the culprit resolves to a fail
   and the paired expression to a pass, both with margin ≥ 15% of threshold; in (b)/(d) the
   intended values are string-present and the culprit is present (d) / absent (b) as specified;
   in (a) none of the 3 policy values are string-present.

## Budget

240 items × 3 models × 2 probes (WHICH, WHICH-ABSTAIN) + 60 (c) items × 3 × 1 (DIRECT-ARITH)
= 1,620 calls. Hard cap 3,000/model. Estimated < $1.5. Idempotent — re-running is a no-op.
Smoke-test 3 items end-to-end and read raw outputs before the full spend.
