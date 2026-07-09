# Exact verification map

Every script in this directory is stdlib-only and exits 0 only when its pinned checks pass.
The scripts establish finite computations or support written proofs; they are not evidence for
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

The definitions, proofs, scope restrictions, failed conjectures, and open obligations live in
[`../theory/certificate-continuation-research-ledger.md`](../theory/certificate-continuation-research-ledger.md).
Regression coverage lives in
[`../tests/test_certificate_continuation.py`](../tests/test_certificate_continuation.py).

Run the package directly:

```bash
python3 proofs/certificate_continuation.py
python3 proofs/certificate_continuation_naive.py
python3 proofs/certificate_priority_theorem.py
python3 proofs/certificate_congruence_counterexamples.py
python3 proofs/versioned_memory_contract.py --max-horizon 4
python3 proofs/checkpoint_frontier_theorem.py
python3 proofs/certificate_access_tradeoff.py
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
