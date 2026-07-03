#!/usr/bin/env python3
"""Shelf Width Law — exact verification (self-contained).

Claim: the witness quotient Q_(k,p) fibers over the answer quotient M_k
(note M_k = Q_(k,1)), and the post-closure mirage-shelf width equals the
answer-weighted fiber entropy:

    omega_closed(k, p) = log2( |Q_(k,p)| / |M_k| )
                       = log2( sum_{d=0}^{k} (d+2)^p / sum_{d=0}^{k} (d+2) )

MEASURED values below are transcribed from the stark repository artifact
results/quotient-thresholds/separator-closure-experiment/separator_closure_experiment.md
(post-closure shelf width column, reported to 3 decimals), where they were
computed by exhaustive separator closure, independently of this formula.

Exit code 0 iff every prediction matches the measurement to reported precision.
"""
import math
import sys


def Q(k: int, p: int) -> int:
    """Protected-witness quotient state count (p=1 gives the bare M_k)."""
    return sum((d + 2) ** p for d in range(k + 1))


def shelf_width_predicted(k: int, p: int) -> float:
    return math.log2(Q(k, p) / Q(k, 1))


# (k, p, measured post-closure shelf width in bits, from stark closure artifact)
MEASURED = [
    (3, 1, 0.000),  # M_3: no fiber, no shelf
    (3, 2, 1.948),
    (4, 2, 2.170),
    (5, 3, 4.858),
]


def main() -> int:
    ok = True
    print(f"{'family':10}{'|Q|':>6}{'|M|':>6}{'predicted':>12}{'measured':>10}  verdict")
    for k, p, measured in MEASURED:
        pred = shelf_width_predicted(k, p)
        match = abs(round(pred, 3) - measured) < 1e-9
        ok &= match
        label = f"Q_({k},{p})" if p > 1 else f"M_{k}"
        print(f"{label:10}{Q(k,p):>6}{Q(k,1):>6}{pred:>12.6f}{measured:>10.3f}  "
              f"{'MATCH' if match else 'MISMATCH'}")
    print("\nShelf Width Law:", "VERIFIED on all closure families" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
