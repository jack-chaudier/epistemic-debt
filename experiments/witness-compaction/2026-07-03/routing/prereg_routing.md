# Phase D preregistration — abstention-delta as a live debt router

Fixed 2026-07-03, before any Phase D API call.

## Question

v5/transfer established abstention as a near-perfect *detector* of artifact-borne debt (uptake ≈ 0.8–0.95 on lost, ≈ 0 on retained). This phase closes the loop: use the abstention signal to **route** — answer from cheap compacted notes when the reader is confident, re-expand to the archived full document only when it abstains. If the detector is as good as measured, this yields near-full justified accuracy at a fraction of full-context cost: a deployable context-engineering primitive (compact aggressively; let calibrated abstention trigger retrieval).

## Design

Model: grok. Items: 30 DENIED v5 items. Inputs reused from cache: grok's v5 15-word notes and its WHICH-ABSTAIN responses (the router signal; no new calls). New calls:

- **always-full baseline**: WHICH asked with policy + full document, all 30 items (30 calls) — accuracy ceiling and token denominator.
- **routed second pass**: for items whose cached WHICH-ABSTAIN was INSUFFICIENT_EVIDENCE, ask WHICH with policy + full document (≈ 18 calls).

Routed pipeline answer = cached notes WHICH-ABSTAIN if it named a parameter, else the second-pass answer. Cost accounting: prompt+completion tokens of the notes-side probes (cached, counted) + second-pass calls, vs 30 always-full calls.

## Preregistered predictions

- **P-D1 (re-expansion restores justification)**: WHICH accuracy on routed (re-expanded) items ≥ 0.85.
- **P-D2 (end-to-end justified accuracy)**: routed-pipeline WHICH accuracy over all 30 DENIED ≥ 0.85, and within 0.10 of the always-full baseline. (Notes-only baseline: 8/30 ≈ 0.27.)
- **P-D3 (it's cheaper)**: routed-pipeline total tokens ≤ 0.75 × always-full total tokens. Caveat preregistered: this corpus is debt-heavy by construction (routing fires on ~60% of items); savings scale as (1 − abstention rate), so the measured ratio is a *worst-case-like* bound for this protocol — the ratio formula is reported alongside.

## Exploratory

False-confidence cost (items answered from notes but wrong); router precision/recall against the lost/retained ground truth; behavior on APPROVED items if extended.

## Budget

≤ 100 calls, grok only.
