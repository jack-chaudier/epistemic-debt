"""Section-obstruction regression: the Vorob'ev/contextuality exact check must stay fixed.

Fast targeted assertions only (the full sweep, incl. the 1.9M-family tetrahedron
enumeration, runs in proofs/section_obstruction.py itself; ~5s, exit 0 iff verified).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "proofs"))

from section_obstruction import (  # noqa: E402
    EQ2, NEQ2, Cover, analyze_family, check_tetra_ternary, cycle_holonomy,
    gyo_acyclic, rip_ordering_exists,
)


def test_acyclicity_implementations_agree_on_known_covers():
    triangle = [(0, 1), (1, 2), (0, 2)]
    filled = triangle + [(0, 1, 2)]
    path = [(0, 1), (1, 2), (2, 3)]
    tetra = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]
    for cover, acyclic in ((triangle, False), (filled, True),
                           (path, True), (tetra, False)):
        assert gyo_acyclic(cover) == rip_ordering_exists(cover) == acyclic


def test_acyclic_covers_have_no_obstruction_exhaustively():
    # Vorob'ev direction on the two smallest acyclic covers, full enumeration.
    for name, n, ctxs in (("P4", 4, [(0, 1), (1, 2), (2, 3)]),
                          ("filled", 3, [(0, 1), (1, 2), (0, 2), (0, 1, 2)])):
        counts = Cover(name, n, ctxs).sweep()
        assert counts["logical"] == counts["strong"] == 0


def test_cycle_shelf_counts_are_exactly_the_holonomy_violations():
    # Strong shelves on C3/C4 = 2^(k-1); every one is a parity violation.
    assert Cover("C3", 3, [(0, 1), (1, 2), (0, 2)]).sweep()["strong"] == 4
    assert Cover("C4", 4, [(0, 1), (1, 2), (2, 3), (0, 3)]).sweep()["strong"] == 8
    for k in (3, 4):
        law_holds, violations = cycle_holonomy(k)
        assert law_holds and violations == 1 << (k - 1)


def test_canonical_specker_triangle_is_answer_determined_shelf():
    c3 = Cover("C3", 3, [(0, 1), (1, 2), (0, 2)])
    res = analyze_family(c3, [NEQ2, NEQ2, NEQ2])
    assert res["compatible"] and res["strong"] and res["deny_determined"]


def test_pr_box_shelf_and_cycle_cut_repayment():
    c4 = Cover("C4", 4, [(0, 1), (1, 2), (2, 3), (0, 3)])
    assert analyze_family(c4, [EQ2, EQ2, EQ2, NEQ2])["strong"]
    path = Cover("P4", 4, [(0, 1), (1, 2), (2, 3)])
    cut = analyze_family(path, [EQ2, EQ2, EQ2])
    assert not cut["logical"] and cut["n_global"] == 2


def test_tetrahedron_ternary_mod3_instance_is_strongly_contextual():
    assert check_tetra_ternary()
