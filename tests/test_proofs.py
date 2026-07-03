"""Exact-model regression tests: the two proved/measured results must stay fixed."""
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "proofs"))
sys.path.insert(0, str(REPO / "proofs" / "vendor"))

from shelf_width_law import Q, shelf_width_predicted, MEASURED  # noqa: E402


def test_fibration_base_is_bare_quotient():
    # M_k = Q_(k,1) = (k+1)(k+4)/2 — the fibration reading.
    for k in range(1, 8):
        assert Q(k, 1) == (k + 1) * (k + 4) // 2


def test_shelf_width_law_matches_closure_artifacts():
    for k, p, measured in MEASURED:
        assert abs(round(shelf_width_predicted(k, p), 3) - measured) < 1e-9


def test_honesty_tax_accounting_identity_and_known_values():
    from honesty_tax import forced_optimal_partition, evaluate
    import exact_pareto_frontier as epf

    model = epf.build_probe_joint_model(3, 2)  # small: 7 rows, fast
    # Known values from the 2026-07-03 run (Q_(3,2) at 2 bits, forced-optimal layout).
    res = forced_optimal_partition(model, 4)
    A_f, J, C = evaluate(model, res[2])
    D, tax = A_f - J, J - C
    assert abs((A_f - C) - (D + tax)) < 1e-12          # accounting identity
    assert abs(A_f - 0.9877) < 5e-4
    assert abs(D - 0.0343) < 5e-4
    assert tax > 2 * D                                  # rate-1 conservation refuted
    # At the joint threshold everything is exact and the tax vanishes.
    res_full = forced_optimal_partition(model, 7)
    A_f, J, C = evaluate(model, res_full[2])
    assert (A_f, J, C) == (1.0, 1.0, 1.0)
