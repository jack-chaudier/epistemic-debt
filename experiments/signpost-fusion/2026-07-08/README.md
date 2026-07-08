# B5a — Fusion-Contract Pilot (2026-07-08)

**Question.** The mirage shelf = the verdict survives compaction while the deciding witness value
dies, so decision accuracy ≫ WHICH accuracy (Δ). Hypothesis (NEXT.md B5a): the shelf exists
because verdict-bearing gist and witness value are **separable strings** in the artifact. A
**fusion contract** on the compactor — *"never state an evaluative/verdict-bearing claim without
its deciding value in the same clause; if you cannot afford the value, drop the claim entirely"* —
makes them survive or die together, so Δ should collapse **by construction, at a matched budget**.

**Two conditions**, same corpus (3 confound-guarded domains × 30 = 90 items, 45 DENIED; selfcheck
0 problems), same probes (compress → decision → WHICH, corrected last-`PARAMETER:` parser), same
predictions P-FU-1…4 (frozen in `prereg_fusion.md` / `prereg_fusion_v2.md`):
- **v1 — 40-word nominal budget** (matched to iterated-compaction). Frozen first.
- **v2 — 15-word nominal budget** (the shelf regime of the highpower/domains campaigns). Frozen
  before its calls; adds a **regime-applicability guard**: a cell tests P-FU-1 only if the control
  arm actually destroys the witness on ≥ 10 / 45 DENIED items (`n_lost ≥ 10`).

Models: grok (`grok-4-1-fast-non-reasoning`), haiku (`claude-haiku-4-5`), gpt (`gpt-4.1-mini`),
temperature 0, idempotent cache, hard cap 3000/model. Candidate set **disclosed** (policy_text) —
deployed-behavior measurement, identical across arms.

## Results

Δ = decision_acc(DENIED) − WHICH_acc(DENIED). S = failing-value survival on DENIED. rlzW = mean
realized words. incoh = DENIED asserted with `PARAMETER: NONE`. unm = WHICH UNMATCHED (parser).

### v1 — 40 words (loose budget: no shelf, non-discriminative)

| model/arm | decD | whichD | S | J | Δ | incoh | rlzW | n_lost | unm |
|---|---|---|---|---|---|---|---|---|---|
| grok/control | 0.911 | 0.644 | 0.978 | 0.600 | **0.267** | 0.00 | 45.3 | 1 | 12 |
| grok/fusion  | 0.956 | 0.644 | 1.000 | 0.622 | 0.311 | 0.00 | 56.3 | 0 | 15 |
| haiku/control| 0.933 | 0.822 | 0.778 | 0.778 | **0.111** | 0.11 | 51.8 | 10 | 1 |
| haiku/fusion | 1.000 | 0.911 | 1.000 | 0.911 | 0.089 | 0.00 | 62.7 | 0 | 4 |
| gpt/control  | 0.956 | 0.911 | 0.956 | 0.911 | **0.044** | 0.00 | 58.4 | 2 | 2 |
| gpt/fusion   | 1.000 | 0.933 | 1.000 | 0.933 | 0.067 | 0.00 | 63.1 | 0 | 3 |

At 40 nominal words the compactor overshoots to 45–58 realized words and keeps essentially all 12
short readings, so control S = 0.78–0.98 and only 1 / 10 / 2 of 45 DENIED items lose the witness.
**There is no mirage to collapse** → P-FU-1 is non-discriminative (grok/gpt inapplicable under the
regime guard; haiku applicable but Δ already small). grok's residual Δ is *not* a shelf: it is the
WHICH abbreviation-parser artifact (confound #2) — 12 UNMATCHED clinical acronyms (SBP, CrCl,
LVEF, eGFR) with the failing value fully surviving. **Clean positive:** fusion drives S → 1.0 with
0 lost witnesses on all 3 models at ≤ 1.25× realized words (P-FU-3 holds here), and removes
haiku's incoherence (0.11 → 0). Fusion works as a witness-retention instruction even at 40w.

### v2 — 15 words (shelf regime: all 3 applicable, n_lost 10 / 23 / 19)

| model/arm | decD | whichD | S | J | Δ | incoh | rlzW | n_lost | unm |
|---|---|---|---|---|---|---|---|---|---|
| grok/control | 0.867 | 0.444 | 0.778 | 0.444 | **0.422** | 0.11 | 25.0 | 10 | 9 |
| grok/fusion  | 0.911 | 0.622 | 1.000 | 0.556 | 0.289 | 0.00 | 42.0 | 0 | 16 |
| haiku/control| 0.911 | 0.578 | 0.489 | 0.556 | **0.333** | 0.22 | 27.3 | 23 | 3 |
| haiku/fusion | 1.000 | 0.889 | 0.978 | 0.889 | 0.111 | 0.00 | 51.3 | 1 | 5 |
| gpt/control  | 1.000 | 0.556 | 0.578 | 0.556 | **0.444** | 0.22 | 23.9 | 19 | 3 |
| gpt/fusion   | 1.000 | 0.933 | 1.000 | 0.933 | 0.067 | 0.00 | 43.3 | 0 | 3 |

At 15 nominal words control finally enters the shelf regime: naked-gist summaries ("all systems
nominal", "no open issues") drop the values, so S falls to 0.49–0.78, incoherence rises to
0.11–0.22, and Δ opens to 0.33–0.44. Fusion collapses it: S → 0.98–1.00, incoherence → 0, Δ →
0.07–0.29. **P-FU-1 passes on haiku and gpt** (Δ at least halved), fails on grok. **But it is not
free:** fusion **ignores the word budget** — realized 42 / 51 / 43 words vs control's 25 / 27 / 24,
a 1.68 / 1.88 / 1.81× overshoot — so **P-FU-3 fails 3 / 3**. The gap collapses because the contract
makes the compactor *refuse to compress*, not because gist and witness were re-fused within the
same budget.

### Prediction scorecard (pass/fail)

| | grok 40w | haiku 40w | gpt 40w | grok 15w | haiku 15w | gpt 15w |
|---|---|---|---|---|---|---|
| P-FU-1 gap collapse (Δ_fus ≤ ½Δ_ctrl) | n/a¹ | **FAIL** | n/a¹ | FAIL² | **PASS** | **PASS** |
| P-FU-2 no unwitnessed confidence | PASS | PASS | PASS | PASS | PASS | PASS |
| P-FU-3 length guard (rlzW_fus ≤ 1.25×) | PASS | PASS | PASS | **FAIL** | **FAIL** | **FAIL** |
| P-FU-4 survival (S_fus ≥ S_ctrl+0.15) | FAIL³ | PASS | FAIL³ | PASS | PASS | PASS |

¹ inapplicable — control n_lost < 10, no shelf. ² grok Δ contaminated by the acronym parser
artifact (unm 9→16) **and** its degenerate always-DENY prior (nonotes_deny 1.0), so its
DENIED-side Δ is prior-driven, not knowledge-driven — a poor P-FU-1 vehicle under the frozen
parser (dual-judge follow-up flagged). ³ S already ≥ 0.96 in control, so a +0.15 rise is
arithmetically impossible — an artifact of the loose regime, not a failure of fusion.

## Verdict

**The strong hypothesis — "fusion collapses the gap by construction at a matched budget" — is
REFUTED. The mechanism it names is real; the "matched budget" is not.**

- **Mechanism confirmed (P-FU-2 6/6, P-FU-4 4/4 where measurable):** the shelf really is
  separable gist + witness strings. Banning naked gist forces witnesses to survive (S → ~1.0) and
  eliminates unwitnessed confidence (incoherence → 0) on every model, at both budgets.
- **Gap does collapse where a shelf exists (P-FU-1 2/3 at 15w: gpt Δ 0.44→0.07, haiku 0.33→0.11).**
- **But not for free (P-FU-3 0/3 at 15w).** The fusion contract and a tight word budget are in
  direct conflict, and **the fusion rule wins in all three models** (instruction-hierarchy
  finding): told both "never claim without the value" and "15 words", the compactor keeps the
  values and blows the budget 1.7–1.9×. Fusion is therefore empirically a **witness-preservation /
  value-dense instruction** (cf. the witness-compaction campaign) dressed as a prose register — it
  buys the gap with realized length, not by re-fusing within the budget. **Deployable fusion needs
  enforced truncation** (hard token cap on the compactor), which reconnects to the realized-vs-
  instructed-budget note in NEXT.md's parking lot: contracts must be specified in realized tokens.

## Confounds found / handled

1. **Realized-vs-instructed budget (headline).** The 40w overshoot hid the shelf entirely (v1
   non-discriminative); at 15w the overshoot *is the mechanism* by which fusion works. Realized
   words reported per arm and guarded by P-FU-3.
2. **WHICH abbreviation-parser artifact (#2), grok.** unm 9→16 (15w) with witnesses surviving —
   inflates grok's Δ and sinks its whichD independent of fusion. Surfaced (never binned); grok's
   phenotype claim flagged for a semantic dual-judge follow-up, not trusted on the frozen parser.
3. **Degenerate always-DENY prior (P-E), grok.** nonotes_deny = 1.0 → grok's DENIED-side decision
   accuracy is information-free, so route-B of P-FU-2 cannot fire and its Δ is prior-driven.
4. **Candidate-set disclosure (#3).** policy_text discloses the 3 candidates (deployed-behavior
   choice), so whichD ≥ S by elimination in both arms; identical across arms, cannot manufacture a
   between-arm contrast. Stated in prereg.
5. **Concurrent-writer dedup.** A duplicate run briefly co-wrote responses_raw.jsonl; 44 keys
   duplicated and 6 grok/clinical 15w compress records diverged (temp-0 non-determinism). Those 6
   items' 15w triples were deleted and regenerated to consistency; file re-verified 0 dup / 0
   mismatch before scoring.

## Cost

$1.64 total (grok $0.14, haiku $1.25, gpt $0.25) over both budgets. Well under the $5 cap.

## Files

`gen_items.py` · `items.jsonl` (90) · `prereg_fusion.md` (v1 + frozen 15w addendum) ·
`prereg_fusion_v2.md` · `runner.py` (smoke/run/score, both budgets) · `responses_raw.jsonl` ·
`scored.csv` (1080 per-item rows) · `fusion_results.json` · this README.
