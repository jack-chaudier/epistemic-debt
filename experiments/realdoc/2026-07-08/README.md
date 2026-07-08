# Real-document tier — external validity (2026-07-08)

**Question (NEXT.md queue 7, "the last big fear").** Every result so far lives on synthetic policy
documents. Does the answer/justification dissociation — and the fusion fix (B5a) — survive **real
prose**? This is the experiment that can invalidate the production roadmap, so a negative result is
reported with full prominence.

**Method — semi-synthetic injection.** 12 real public-domain **NTSB aviation-accident *Analysis***
narratives (US federal government works, public domain; provenance + URLs in `SOURCES.md`,
302–573 words each, 6 regions, 2005–2022, fatal/limited/factual) with 3 decision-relevant policy
readings injected into the natural prose at varied positions (`gen_items.py`). Ground truth fully
controlled (verdict = conjunction of 3 injected thresholds); linguistic texture real. Framing: an
airworthiness / return-to-service review — the accident narrative is the occurrence summary, the
injected readings are investigation/maintenance findings in the register NTSB analyses already use
(postaccident examinations routinely quote instrument readings). **12 sources × 5 policy variants =
60 items** (30 APPROVED / 30 DENIED; selfcheck 0 problems).

**Design.** 2 arms (CONTROL = contract-blind compaction; FUSION = the exact signpost-fusion contract)
× 2 clean-parser models (haiku, gpt; grok skipped — acronym artifact). Fixed **nominal 15-word**
budget (shelf regime; a realistic fixed deployed-compactor spec). Probes: decision, WHICH (corrected
last-`PARAMETER:` parser), nonotes prior. Candidate set disclosed (deployed-behavior). Predictions
frozen in `prereg_realdoc.md` **after** a 3-item smoke (items 000–002, cached) confirmed the budget.

## Results

Δ = decision_acc(DENIED) − WHICH_acc(DENIED). S = failing-value survival on DENIED. decA =
decision accuracy on APPROVED items. incoh = DENIED asserted with `PARAMETER: NONE`. rlzW = mean
realized words. n_lost = DENIED items whose deciding witness died in compaction.

| model/arm | decD | decA | whichD | S | J | Δ | incoh | rlzW | n_lost |
|---|---|---|---|---|---|---|---|---|---|
| haiku/control | 0.867 | **0.000** | 0.000 | 0.000 | 0.000 | **0.867** | 0.700 | 20.5 | 30/30 |
| haiku/fusion  | 0.967 | 0.333 | 0.667 | 0.667 | 0.667 | 0.300 | 0.300 | 41.2 | 10/30 |
| gpt/control   | 1.000 | **0.000** | 0.067 | 0.033 | 0.067 | **0.933** | 0.867 | 16.0 | 29/30 |
| gpt/fusion    | 0.967 | 0.267 | 0.800 | 0.700 | 0.767 | 0.167 | 0.200 | 21.2 | 9/30 |

**The dissociation replicates on real prose — and is *sharper*, not weaker.** Under contract-blind
compaction the 15-word summary is a summary of the **accident**, not of the readings: it drops every
injected witness (S → 0.00 / 0.03; n_lost 30 / 29 of 30) and the reader's verdict follows the
narrative's negative valence. **gpt returns DENIED on all 60 items; haiku on 27/30 APPROVED (the rest
abstain).** So control `decA = 0.000` on both models: the answer channel that survives compaction of
real accident prose is a **content-free crash → DENY reflex**, correct on DENIED only by coincidence.
Justification collapses in lockstep (whichD ≈ 0, incoherence 0.70 / 0.87 — DENIED asserted with no
nameable cause). This is the mirage shelf in full, and worse than the synthetic version, where the
surviving verdict at least tracked policy.

**Fusion recovers genuine policy reasoning — partially.** Banning naked gist forces the witnesses back
into the summary: S 0.00→0.67 / 0.03→0.70, WHICH-correct on DENIED 0→20/30 (haiku) and 2→24/30 (gpt)
tracking witness survival ≈ 1:1 (J 0.00→0.67 / 0.07→0.77), incoherence at least halved (0.70→0.30,
0.87→0.20), and APPROVED-side accuracy lifts off the floor (0.00→0.33 / 0.27). **But fusion is only
partial on real prose:** ~500-word documents at a 15-word budget overflow even fusion's
witness-retention — realized 41 / 21 words (2.01× / 1.32× the control length, the known budget
override) yet still S ≈ 0.67–0.70, not the ≈ 1.0 fusion reached on the shorter synthetic docs. So
n_lost stays at 9–10, incoherence does not reach 0, and the accident gist still suppresses APPROVED
accuracy below 0.35. Deployable fusion on real long documents needs a larger realized budget or the
enforced-truncation-with-selection successor (signpost B5a follow-up).

### Prediction scorecard (frozen in prereg_realdoc.md; per model, regime guard satisfied — n_lost ≥ 10)

| | haiku | gpt |
|---|---|---|
| **P-RD-1** dissociation replicates (control Δ ≥ 0.20) | **PASS** (0.867) | **PASS** (0.933) |
| **P-RD-2** incoherence appears (control incoh ≥ 0.05) | **PASS** (0.700) | **PASS** (0.867) |
| **P-RD-3** fusion kills it (incoh_fus ≤ ½ incoh_ctrl) | **PASS** (0.30 ≤ 0.35) | **PASS** (0.20 ≤ 0.43) |
| **P-RD-4** witness lift (S_fus ≥ S_ctrl + 0.15) | **PASS** (0.67) | **PASS** (0.70) |
| realized-length ratio (disclosed, not a prediction) | 2.01× | 1.32× |

**4/4 on both models.** Per the prereg verdict rule (P-RD-1 & P-RD-2 pass on ≥ 1 applicable model and
the fusion mechanism reproduces), **external validity is UPHELD**: the shelf and the fusion fix both
transfer to real prose.

## Verdict

**The roadmap survives its external-validity test — with one sharpening the synthetic corpus hid.**
On real accident narratives the dominant, salient content is the *story*, not the decision-relevant
readings, so contract-blind compaction preserves an accident-valence gist and the reader's verdict
becomes a **content-free crash → DENY reflex** (decA = 0 on both models) while the justification is
destroyed. The answer/justification gap is therefore not merely reproduced on real prose but
*amplified*: the surviving "answer" is unreliable in a way string-survival S already predicted (S → 0)
but decision accuracy on DENIED items alone (0.87–1.00) would badly overstate. **Reporting justified
accuracy J (0.00 / 0.07) rather than decision accuracy is essential precisely here** — the metric the
program advocates is what exposes the failure. Fusion restores J to 0.67–0.77 and pulls the verdict
back toward policy, confirming the mechanism, but only partially at a fixed short budget: on real long
documents the witness-retention it buys costs realized length, and even then does not fully fit.

## Confounds found / handled

1. **Value-collision with source numerals (NEW real-doc confound).** Every injected value is uniquely
   `retained()` among all numerals in the final document (source narrative numbers + the 3 injected);
   the failing value is a unique string. Enforced by `gen_items.selfcheck` (0 problems) and pinned by
   `tests/test_realdoc_artifacts.py`. Required a collision-robust param bank + triple-resample (small
   aviation magnitudes collided with ubiquitous small numbers in the prose).
2. **Accident-outcome gist bias (the headline confound — measured, disclosed, preregistered).** Real
   narratives carry a strong negative-valence gist ("in-flight breakup", "substantial damage").
   Decorrelated from truth by construction (each source appears 5× with a balanced verdict), so it
   cannot manufacture the gap — but it *drives* the surviving verdict (control decA = 0, nonotes-deny
   0.40 / 0.63). This is the P-D2 gist-belief mechanism observed in the wild; it makes the real-prose
   failure sharper than synthetic, not an artifact to be scrubbed.
3. **Injected-sentence verdict leak.** The 3 injected findings scanned with `domains.VERDICT_WORDS`
   (clean). The real narrative is deliberately **not** scrubbed — it is uncontrolled real prose about
   a different subject and decorrelated from truth.
4. **Candidate-set disclosure (#3).** policy_text discloses the 3 candidates; identical across arms.
   WHICH ≥ S by elimination in both arms (cannot manufacture a between-arm contrast).
5. **Parser artifact (#2).** grok excluded; haiku/gpt on the corrected last-anchor parser; WHICH
   UNMATCHED = 0 on both arms/models (surfaced, none binned).

## Cost

**$0.4576** total (haiku $0.3905, gpt $0.0671) over 840 probe calls. Well under the $8 cap.

## Proposed ledger row (for the lead to insert into results/RESULTS.md — do not edit that file here)

```
| 2026-07-08 | **Answer/justification dissociation survives REAL prose (external-validity tier), and is sharper**: 12 public-domain NTSB accident narratives with 3 policy readings injected into natural text (60 items, 30/30). Contract-blind 15-word compaction summarizes the *accident*, drops every witness (S→0.00/0.03) → verdict becomes a content-free crash→DENY reflex (decision_acc on APPROVED = **0.00** both models; DENIED-side 0.87/1.00 is prior-driven), justification destroyed (WHICH≈0, incoherence 0.70/0.87). Fusion contract recovers it (S→0.67/0.70, WHICH 0→20/24 of 30, J 0.00→0.67/0.77, incoherence halved) but only **partially** at a fixed short budget (realized 1.3–2.0×, S<1). Justified accuracy J, not decision accuracy, is what exposes the failure. | PREREGISTERED (P-RD-1..4 4/4 both models; regime guard n_lost≥10 satisfied) | haiku+gpt, 60 items × 2 arms, 840 calls, $0.46 | [realdoc](../experiments/realdoc/2026-07-08/README.md) |
```

## Files

`SOURCES.md` (provenance) · `sources/` (12 verbatim NTSB Analysis texts) · `sources.jsonl` ·
`build_sources.py` · `gen_items.py` (injection + selfcheck) · `items.jsonl` (60) ·
`prereg_realdoc.md` (frozen) · `runner.py` (smoke/run/score) · `responses_raw.jsonl` (840) ·
`scored.csv` (240 per-item rows) · `realdoc_results.json` · this README.
