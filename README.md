# justification-gap

**A resource theory of being right for reasons.** Correctness and justification are different physical resources with a computable exchange rate. Under memory/context pressure, systems keep correct answers after losing the reasons for them (the *mirage shelf*); this repo develops the exact theory, the falsifiable laws, and the LLM experiments.

Successor / consolidation of the mirage program (`stark`, `dreams`, `mirage`, …). The theory core lives in [theory/justification-gap-program.md](theory/justification-gap-program.md).

## Results so far (2026-07-03)

| # | Result | Status | Artifact |
|---|--------|--------|----------|
| 1 | **Shelf Width Law**: `M_k = Q_(k,1)`; Q fibers over M; post-closure shelf width `= log2(\|Q\|/\|M\|)` (fiber entropy) | EXACT — verified 3/3 closure families | [proofs/shelf_width_law.py](proofs/shelf_width_law.py) |
| 2 | **Rate-1 conservation of epistemic debt** | REFUTED (exact) | [proofs/honesty_tax.py](proofs/honesty_tax.py) |
| 3 | **Honesty tax / retrofit gap**: retrofitting abstention onto answer-optimal memory costs 2.5–18× the debt; layouts designed for honesty can cost 0.47×. Faithfulness must be trained in, not bolted on | EXACT (measured on 4 model families) | [proofs/honesty_tax.py](proofs/honesty_tax.py) |
| 4 | **Within-item dissociation on Grok**: verdict survives witness destruction (0.929) while naming-the-reason collapses (0.071, below guessing); non-overlapping 95% CIs | PREREGISTERED, replicated (1 model) | [experiments/grok-pilots/2026-07-03/v4](experiments/grok-pilots/2026-07-03/v4/v4_results.json) |
| 5 | **Incoherence signature**: `DENIED` + "no failing parameter" from the same notes — 12/14 lost-witness vs 0/16 retained | PREREGISTERED, replicated (1 model) | same |
| 6 | **Confabulation locus**: identification probes stay honest (1/14 fabricated); action probes fabricate specifics 14/14 | PREREGISTERED, replicated (1 model) | same |
| 7 | **Abstention as debt detector**: 13/14 uptake on lost witnesses, 0/16 false abstains | PREREGISTERED, replicated (1 model) | same |
| 8 | The surviving verdict is prior/gist, not knowledge (**bias shelf**) — lost-cell accuracy indistinguishable from a degenerate always-DENY prior | OBSERVED (needs calibrated-prior criterion, v5) | same |

Total LLM spend to date: ≈ $0.15 (1,134 calls, grok-4-1-fast-non-reasoning).

## Quickstart

```bash
python3 proofs/shelf_width_law.py     # exact check, no dependencies
python3 proofs/honesty_tax.py         # exact check, stdlib only (~1 min)
python3 -m pytest tests/ -q           # regression + artifact integrity + secret hygiene
```

Experiments need an xAI key: `export XAI_API_KEY=...` (never committed; see CLAUDE.md / AGENTS.md for hygiene rules).

## Layout

```
theory/          the program document: laws, conjectures, theorem targets, appendices A–E
proofs/          exact finite-model verifications (vendor/ = pinned copies of stark modules)
experiments/     LLM experiments; one dated dir per campaign, one vN/ per protocol iteration
results/         RESULTS.md — the evidence ledger (every claim carries a status label)
tests/           pytest: proofs stay fixed, artifacts stay intact, no secrets in tree
```

Every experiment iteration keeps: `runner*.py` (seeded, idempotent response cache, temperature 0, hard call cap), `items.jsonl`, `responses_raw.jsonl`, `scored.csv`, and for confirmatory runs a machine-readable `*_results.json` with preregistered predictions marked pass/fail.

## Roadmap

1. **v5**: calibrated-prior criterion; conjunctive/disjunctive sweep (shelf ∝ answer-quotient coarseness — quantitative theory test).
2. **Multi-model replication** of v4 (Claude, GPT, Gemini, open models). If the incoherence signature and action-channel confabulation generalize, write the paper.
3. **Distillation experiment**: teacher vs distilled student on counterfactual variants (Law 1 at world scale).
4. Formal core: prove the Shelf Width Law in the fibered case; the Honesty Theorem; reposition the transport/holonomy material on Vorob'ev / Abramsky–Brandenburger before any external claim.

## Provenance

Exact-model machinery vendored from [`jack-chaudier/stark`](https://github.com/jack-chaudier/stark) (same author). The 2026-07-03 review of the wider mirage program and the derivation of the results above are recorded in the theory document's appendices.
