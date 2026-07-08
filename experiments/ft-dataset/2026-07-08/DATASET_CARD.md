# Calibrated-reader SFT dataset (B4 groundwork) — dataset card

**Date:** 2026-07-08 · **API spend to build: $0** (cached artifacts + deterministic templating).
**Status:** groundwork only — no model trained, no fine-tune launched. Build track item **B4**.

## What this teaches

A reader model's target behavior under compaction: **acknowledge debt instead of confabulating.**
Given a policy plus compressed case notes, the calibrated reader should

1. **decision channel** — assert a verdict only when the deciding value survives in the notes;
   when it does not, give the **policy-conservative verdict (DENIED — cannot confirm approval)**
   with an **explicit missing-data flag** naming the absent policy value(s);
2. **WHICH channel** — when the deciding witness is present, name the failing parameter and cite
   its value; when it is absent, say the specific value is **not in the notes** (the
   `NONE_MISSING_DATA` phenotype) rather than confabulating a parameter or asserting "nothing
   failed";
3. **witness present** — answer plainly and **fuse the value into the claim** (B5c register:
   witnessed claims assert flatly, unwitnessed claims are flagged).

This is haiku's *native* phenotype (coherent debt-acknowledgment 0.79 vs grok/gpt 0.00, rescore
2026-07-06 rows 11/20/30). The dataset distils that behavior as an explicit training target so it
can be bought cheaply in a small open-weight or `gpt-4.1-mini` reader (honesty-premium prediction).

## Provenance

Built by `build_dataset.py` from three cached campaigns — **compaction (`compress*`) calls only;
no reader responses are used** (see exclusion rule):

| corpus | path | notes source (call types) | domains |
|---|---|---|---|
| highpower | `experiments/highpower/2026-07-06/` | `compress` (15-word) | ops_incident ×400 |
| domains | `experiments/domains/2026-07-06/` | `compress` (15-word) | 6 domains ×100 |
| fusion | `experiments/signpost-fusion/2026-07-08/` | `compress_{ctrl,fus,ctrl15,fus15}` (40w + 15w, control & fusion register) | ops/clinical/ci ×30 |

The reader **input** reproduces the deployed dissociation protocol verbatim:
`policy_text + "\n\nCompressed case notes:\n" + <cached summary> + "\n\n" + <canonical variant-0 probe>`.
The two probes (`DECISION`, `WHICH`) are copied verbatim from `experiments/lib/dissociation.py`
(pinned by `tests/test_ft_dataset.py`).

Witness-present/absent is decided by the **existing `retained()`** numeric-survival check
(`grok-pilots/.../runner3.py`) — the same function the campaigns scored with.

## Gold-response templates (deterministic, from item ground truth)

Every gold is templated; **no API call, no model output, is ever copied into a label.**

| class | trigger | gold shape |
|---|---|---|
| `CITED_DENIED` (decision) | truth DENIED, failing value **retained** | `ANSWER: DENIED` + "The `<param>` is `<v> <u>`, {above/below} the policy {max/min} of `<thr> <u>` …" |
| `CONFIRMED_APPROVED` (decision) | truth APPROVED, **all** policy values retained | `ANSWER: APPROVED` + all three conditions cited with values vs thresholds |
| `CONS_MISSING` (decision) | any policy value **absent** | `ANSWER: DENIED` (conservative) + "cannot confirm approval" + `[MISSING DATA: <names>]` |
| `WHICH_CITED` (which) | truth DENIED, failing value **retained** | `PARAMETER: <name>` + value + breach |
| `WHICH_NONE_NO_FAILURE` (which) | truth APPROVED, all policy retained | `PARAMETER: NONE` + "all three conditions satisfied … no parameter failed" |
| `WHICH_NONE_MISSING_DATA` (which) | deciding value **absent** | `PARAMETER: NONE` + "the reading … is not in the notes — `<names>` absent" + `[MISSING DATA: <names>]` |

The `NONE_NO_FAILURE` vs `NONE_MISSING_DATA` split is the row-20 distinction and the scientific
point of the set. The conservative verdict is DENIED because the policy is "APPROVED **only if**
all conditions met" — an unconfirmable condition cannot license approval. Note this means some
truly-APPROVED items whose notes collapsed to bare gist ("all systems nominal") carry a **DENIED**
gold: that is intended — the calibrated reader must not trust asserted normality (the P-D2 gist
trap) over absent values.

## Class balance (committed files)

Total **5,906** examples over **1,077** unique items; held-out split **by item** (no item spans
train/eval): **5,021 train / 885 eval**.

| channel | class | count | share |
|---|---|---|---|
| decision | CITED_DENIED | 967 | 16.4% |
| decision | CONFIRMED_APPROVED | 632 | 10.7% |
| decision | CONS_MISSING | 1,354 | 22.9% |
| which | WHICH_CITED | 967 | 16.4% |
| which | WHICH_NONE_MISSING_DATA | 1,354 | 22.9% |
| which | WHICH_NONE_NO_FAILURE | 632 | 10.7% |

By corpus: highpower 2,120 · domains 1,774 · fusion 2,012. By notes-model: grok 1,752 · haiku
2,032 · gpt 2,122. The dominant missing-data class is deterministically capped at 1.4× the cited
count per channel (`MISSING_CAP_RATIO`, seed `8072026`) so `NONE_NO_FAILURE` lands at the
requested ~10%; the missing-data phenotype still leads, which is correct — it is the behavior most
in need of teaching. ~1.6M training tokens per epoch (≈322 tok/example).

## Exclusion rule (grok parser artifact)

**Structural:** we distil **no reader responses**, so the grok WHICH parser artifact (rescore
2026-07-06: verbose/abbreviated answers scored `UNMATCHED`, a *reader-scoring* bug) cannot enter
the labels at all — gold comes from item ground truth, not from what any model answered.

**Data-level guard:** `excluded(corpus, model)` drops **grok as a notes-source in the `domains`
corpus**. That corpus is the documented artifact locus: grok abbreviates parameter *names* to
acronyms there (`trig`/`QTc`/`ALT`/`DTI`/`LTV`), so a name-citing gold would sit over a note
surface that never spells the parameter out. Values survive numerically (so `retained()` stays
valid), but we exclude these notes to keep every citation-bearing gold grounded in an
abbreviation-free surface. grok notes in **highpower** (ops, no acronyms) and **fusion** are kept;
haiku/gpt kept everywhere. The selfcheck asserts no excluded source reaches the output.

## Known limitations

- **Synthetic corpora.** All three campaigns are template-generated ops/clinical/finance records
  with planted ground truth. External validity is gated by the real-document tier (NEXT queue 7);
  a reader tuned here is validated *in-distribution* until that lands.
- **`retained()` is a numeric heuristic.** It flags a value as surviving if any number within 1%
  appears in the notes; dense summaries (11–12 packed numbers) carry a small false-positive risk,
  so a few `CITED` golds may cite a value that is coincidentally present. Same method the
  campaigns scored with; a semantic witness check would tighten it.
- **Two channels only** (decision, WHICH). The repair channel and multi-hop recovery probes are
  out of scope for v1.
- **Conservative-DENIED convention** is policy-specific ("APPROVED only if"). A different policy
  logic (e.g. "DENIED only if") would flip the conservative default; the template hard-codes the
  campaigns' convention.
- **Gist-trap golds** relabel some truly-APPROVED items as DENIED (see above). This teaches
  calibration, not the ground-truth verdict — evaluate accuracy against the *calibrated* target,
  not raw item truth, on missing-witness cells.

## Reproduce

```bash
python3 build_dataset.py stats       # class balance, no writes
python3 build_dataset.py build       # (re)write dataset_{train,eval}.jsonl — deterministic
python3 build_dataset.py selfcheck   # mechanical gate over the committed files
uv run --with pytest --no-project -- pytest tests/test_ft_dataset.py -q
```

## Proposed NEXT update

> Under **Infinite-context build track → B4**, change status from "design sketch" to:
> **B4a groundwork DONE 2026-07-08** → `experiments/ft-dataset/2026-07-08/`. Deterministic,
> $0-API SFT dataset distilling the calibrated debt-acknowledgment phenotype: 5,906 chat examples
> (5,021 train / 885 eval, split by item) over 1,077 items × 3 corpora × 3 notes-models, six
> gold classes templated from ground truth (cited-witness fusion / conservative missing-data /
> NONE_NO_FAILURE vs NONE_MISSING_DATA). Two training options costed in `training_plan.md`
> (OpenAI `gpt-4.1-mini` FT ≈ $15–25; open-weight Qwen3-4B QLoRA ≈ $2–5 GPU rental). **Next:** the
> lead authorizes spend → run `launch_openai_ft.py` (or the LoRA config), then the dissociation
> battery before/after with Δ, incoherence, and fusion-register compliance as headline metrics.
