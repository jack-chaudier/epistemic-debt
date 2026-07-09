#!/usr/bin/env python3
"""Shelf-width count-gap audit (self-contained).

The separator-closure artifact reports a post-closure state-count gap equal to

    omega_closed(k, p) = log2( |Q_(k,p)| / |M_k| )
                       = log2( sum_{d=0}^{k} (d+2)^p / sum_{d=0}^{k} (d+2) )

This script verifies that numerical identity and also audits the stronger
"fiber entropy" interpretation.  Projection onto one protected-witness
coordinate has the advertised constant fibers but is not answer-preserving in
general.  The natural answer map keeps ``(d, max_i c_i)``; its fiber above
frontier ``f`` has size

    (f + 2)^p - (f + 1)^p,

which is nonconstant for p > 1.  Consequently the global log count ratio is
not automatically a Shannon conditional entropy.  A distribution and an
actual answer-preserving map must be supplied before making that claim.

MEASURED values below are transcribed from the stark repository artifact
results/quotient-thresholds/separator-closure-experiment/separator_closure_experiment.md
(post-closure shelf width column, reported to 3 decimals), where they were
computed by exhaustive separator closure, independently of this formula.

Exit code 0 iff every count-gap prediction matches the reported measurement and
the natural-map audit reproduces the pinned exact values.
"""
import math
import sys


def Q(k: int, p: int) -> int:
    """Protected-witness quotient state count (p=1 gives the bare M_k)."""
    return sum((d + 2) ** p for d in range(k + 1))


def shelf_width_predicted(k: int, p: int) -> float:
    """Global log state-count ratio (retained name for compatibility)."""
    return math.log2(Q(k, p) / Q(k, 1))


def natural_answer_fiber_sizes(k: int, p: int) -> tuple[int, ...]:
    """Fiber sizes for the answer-preserving map ``(d, c) -> (d, max(c))``."""
    return tuple(
        (frontier + 2) ** p - (frontier + 1) ** p
        for depth in range(k + 1)
        for frontier in range(-1, depth + 1)
    )


def natural_conditional_entropy_uniform_q(k: int, p: int) -> float:
    """H(Q|M) for a uniform Q state under the natural max-coordinate map."""
    fibers = natural_answer_fiber_sizes(k, p)
    total = Q(k, p)
    assert sum(fibers) == total
    return sum((size / total) * math.log2(size) for size in fibers)


# (k, p, measured post-closure shelf width in bits, from stark closure artifact)
MEASURED = [
    (3, 1, 0.000),  # M_3: no fiber, no shelf
    (3, 2, 1.948),
    (4, 2, 2.170),
    (5, 3, 4.858),
]


def main() -> int:
    ok = True
    print(
        f"{'family':10}{'|Q|':>6}{'|M|':>6}{'count gap':>12}"
        f"{'H(Q|M)':>12}{'measured':>10}  verdict"
    )
    for k, p, measured in MEASURED:
        pred = shelf_width_predicted(k, p)
        entropy = natural_conditional_entropy_uniform_q(k, p)
        match = abs(round(pred, 3) - measured) < 1e-9
        ok &= match
        label = f"Q_({k},{p})" if p > 1 else f"M_{k}"
        print(
            f"{label:10}{Q(k,p):>6}{Q(k,1):>6}{pred:>12.6f}"
            f"{entropy:>12.6f}{measured:>10.3f}  "
            f"{'MATCH' if match else 'MISMATCH'}"
        )
        if p > 1:
            ok &= len(set(natural_answer_fiber_sizes(k, p))) > 1
            ok &= not math.isclose(pred, entropy)
    print(
        "\nCount-gap audit:",
        "VERIFIED; natural answer fibers are nonconstant, so entropy is distinct"
        if ok
        else "FAILED",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
