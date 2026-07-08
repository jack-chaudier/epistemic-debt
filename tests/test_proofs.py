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


def test_honesty_premium_reproduces_causal_referee_constants():
    # The premium/retrofit-gap headline numbers (README row 3, theory Appendix A.2)
    # must be reproducible from committed machinery, not just transcribed.
    from honesty_premium import premium_table
    import exact_pareto_frontier as epf

    ref = premium_table(epf.build_dataset_support_model(epf.build_causal_referee_spec()))
    at2 = next(r for r in ref if r["bits"] == 2)
    at3 = next(r for r in ref if r["bits"] == 3)
    assert abs(at2["C_star"] - 0.8317) < 2e-3            # breach-optimal certified mass
    assert abs(at2["premium_over_D"] - 0.469) < 5e-3     # honesty cheaper than the debt
    assert abs(at3["tax_over_D"] - 18.01) < 0.1          # retrofit tax on answer layout
    retrofit_gap = at3["tax_over_D"] / at2["premium_over_D"]
    assert 36.0 < retrofit_gap < 40.0                    # ~38x
    # On every synthetic Q family, by contrast, honesty is never cheaper than the debt.
    for k, p in ((3, 2), (4, 2)):
        rows = premium_table(epf.build_probe_joint_model(k, p))
        assert all(r["premium_over_D"] is None or r["premium_over_D"] > 1.0 for r in rows)


def test_honesty_theorem_exact_witness_vs_certificate_quotients():
    from honesty_theorem import frontier_models, summarize_model

    rows = {row.label: row for row in (summarize_model(model) for model in frontier_models())}
    assert rows["Q_(3,2)"].answer_states == 5
    assert rows["Q_(3,2)"].certificate_states == 6
    assert rows["Q_(3,2)"].exact_witness_states == rows["Q_(3,2)"].joint_states == 7
    assert rows["Q_(4,2)"].certificate_states == 7
    assert rows["Q_(4,2)"].exact_witness_states == rows["Q_(4,2)"].joint_states == 8
    assert rows["Q_(5,3)"].certificate_states == 9
    assert rows["Q_(5,3)"].exact_witness_states == rows["Q_(5,3)"].joint_states == 13
    assert rows["causal_referee"].answer_states == 4
    assert rows["causal_referee"].certificate_states == rows["causal_referee"].joint_states == 15
