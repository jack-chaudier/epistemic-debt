# Exact verification map

The listed scripts are stdlib-only and are run under normal, non-optimized
Python; do not use `python -O` for assertion-bearing legacy validators. The
certificate-continuation validators modified in this pass refuse optimized
execution where their checks depend on assertions. The scripts establish
finite computations or support written proofs; they are not evidence for
claims outside the resource model stated in each module docstring.

## Certificate continuation package

| Artifact | Role |
|---|---|
| `certificate_continuation.py` | Primary E0 partition, transition, reachability, and certificate-soundness validator. |
| `certificate_continuation_naive.py` | Independent raw-state and partition implementation used to reproduce E0. |
| `certificate_continuation_e0_results.json` | Frozen canonical output compared byte-semantically by regression tests. |
| `certificate_priority_theorem.py` | Finite checks supporting the coded `Q_(k,p)` priority-selector and streaming/chunk-composition theorems. |
| `certificate_congruence_counterexamples.py` | Static-versus-online, nonuniqueness, closed-cover, and deletion counterexamples. |
| `versioned_memory_contract.py` | Exact small dynamic contract with versions, revisions, retractions, contradictions, current queries, and temporal queries. |
| `checkpoint_frontier_theorem.py` | Independent event-only checker for the temporal checkpoint factorization law. |
| `certificate_access_tradeoff.py` | Exact finite audit of the active-state/archive-access/fallback transcript bound. |
| `general_contract_search.py` | Finite accepted-output partition/closed-cover solver; a separate direct path-machine enumerator cross-checks the frozen minimum counts, not every generated object. |
| `general_contract_search_naive.py` | Independent BFS-canonical deterministic history-machine enumerator. |
| `linear_obligation_rank.py` | Exact fixed-horizon rank phase and constrained refinement law for binary linear obligation families. |
| `evolving_checkpoint_refinement.py` | Causal-checkpoint and last-window migration algorithms with independent exact replay checks. |
| `certificate_cover_resource.py` | Accepted-output cover curves, proof-component-size eligibility, and a static cover-relaxed necessary simultaneous-query bound. |
| `certificate_verifier_hitting.py` | Exact accepted-proof hitting/cylinder characterization for perfectly sound and complete finite proof systems. |

The definitions, proofs, scope restrictions, failed conjectures, and open obligations live in
[`../theory/certificate-continuation-research-ledger.md`](../theory/certificate-continuation-research-ledger.md).
Regression coverage lives in
[`../tests/test_certificate_continuation.py`](../tests/test_certificate_continuation.py)
and [`../tests/test_infinite_context_boundary.py`](../tests/test_infinite_context_boundary.py).

Run the package directly:

```bash
python3 proofs/certificate_continuation.py
python3 proofs/certificate_continuation_naive.py
python3 proofs/certificate_priority_theorem.py
python3 proofs/certificate_congruence_counterexamples.py
python3 proofs/versioned_memory_contract.py --max-horizon 4
python3 proofs/checkpoint_frontier_theorem.py
python3 proofs/certificate_access_tradeoff.py
python3 proofs/general_contract_search.py
python3 proofs/linear_obligation_rank.py
python3 proofs/evolving_checkpoint_refinement.py
python3 proofs/certificate_cover_resource.py
python3 proofs/certificate_verifier_hitting.py
```

## Earlier exact checks

| Artifact | Role |
|---|---|
| `shelf_width_law.py` | Verifies the checked global count gaps and pins the correction that they are not automatically fiber entropies. |
| `honesty_tax.py` | Exact honesty-tax and conservation checks. |
| `honesty_premium.py` | Exact designed-in honesty premium and retrofit-gap checks. |
| `honesty_theorem.py` | Exact-witness versus one-valid-certificate partition checks. |
| `section_obstruction.py` | Finite contextuality/gluing obstruction sweep. |

Run the complete repository regression suite with:

```bash
uv run --with pytest --no-project -- pytest tests/ -q
```
