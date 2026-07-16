#!/usr/bin/env python3
"""Exact checks for a deterministic archive-access/fallback counting bound.

This file does not claim a new information-theoretic theorem.  It makes the
resource model behind one useful infinite-context lower bound explicit.

Let a fixed query have pairwise-disjoint accepted answer/certificate outputs
on N histories.  A deterministic responder starts with b bits of active state
and may read at most t cells of w bits from a history-dependent exact archive.
The address of each adaptive read is a function of the query, active state,
and earlier cell contents; addresses therefore add no independent transcript
information.  At most 2**(b+t*w) transcripts are possible.

Each transcript can be correct without fallback for at most one of the N
histories, because the accepted output sets are disjoint.  If F histories may
fall back and E may be wrong, then

    b + t*w >= ceil(log2(N - F - E)).

Equivalently, a b-bit, t-probe fast path can be correct on at most
2**(b+t*w) histories.  This is a transcript-capacity bound, not an additive
law involving certificate length: output length is a second bottleneck, not a
substitute for information the responder never accessed.

The executable exhaustively verifies the finite combinatorial core and applies
it to the versioned-memory contract's complete current and all-as-of outputs.
Exit code 0 iff every check passes.
"""
from __future__ import annotations

import itertools
import math
import sys


if not __debug__:
    raise RuntimeError("exact theorem checks require Python assertions; do not use -O")


def ceil_log2(count: int) -> int:
    if count < 1:
        raise ValueError("count must be positive")
    return (count - 1).bit_length()


def transcript_capacity(active_bits: int, probes: int, cell_bits: int) -> int:
    if min(active_bits, probes, cell_bits) < 0:
        raise ValueError("resource counts must be nonnegative")
    return 1 << (active_bits + probes * cell_bits)


def maximum_fast_correct(
    history_count: int,
    active_bits: int,
    probes: int = 0,
    cell_bits: int = 0,
) -> int:
    if history_count < 1:
        raise ValueError("history_count must be positive")
    return min(history_count, transcript_capacity(active_bits, probes, cell_bits))


def minimum_failures(
    history_count: int,
    active_bits: int,
    probes: int = 0,
    cell_bits: int = 0,
) -> int:
    """Minimum fallback-plus-error count forced by transcript capacity."""

    return history_count - maximum_fast_correct(
        history_count, active_bits, probes, cell_bits
    )


def required_transcript_bits(history_count: int, permitted_failures: int = 0) -> int:
    if not 0 <= permitted_failures < history_count:
        raise ValueError("permitted_failures must be in [0, history_count)")
    return ceil_log2(history_count - permitted_failures)


def current_frontier_count(horizon: int, cells: int, values: int) -> int:
    if horizon < 0 or cells < 1 or values < 1:
        raise ValueError("invalid frontier parameters")
    if horizon == 0:
        return 1
    return sum(
        math.comb(cells, populated)
        * math.comb(horizon - 1, populated - 1)
        * values**populated
        for populated in range(1, min(cells, horizon) + 1)
    )


def verify_exhaustive_transcript_core(max_histories: int = 6) -> int:
    """Enumerate transcript assignments and recover the exact capacity law.

    For a fixed assignment, one disjoint accepted output can be selected per
    nonempty transcript fiber.  Its best correct count is therefore the number
    of used transcripts.  Maximizing over all assignments must give min(N, C).
    """

    assignments_checked = 0
    for histories in range(1, max_histories + 1):
        for capacity in range(1, min(4, histories + 1) + 1):
            best = 0
            for assignment in itertools.product(range(capacity), repeat=histories):
                assignments_checked += 1
                best = max(best, len(set(assignment)))
            assert best == min(histories, capacity)
    return assignments_checked


def versioned_boundary_rows(max_horizon: int = 8) -> list[dict[str, int | float]]:
    """Apply the bound to m=4 cells and v=3 publication values."""

    cells = 4
    values = 3
    alphabet = cells * values
    rows: list[dict[str, int | float]] = []
    for horizon in range(1, max_horizon + 1):
        current_states = current_frontier_count(horizon, cells, values)
        exact_histories = alphabet**horizon
        current_bits = ceil_log2(current_states)
        fast_correct = maximum_fast_correct(exact_histories, current_bits)
        forced_fallback = exact_histories - fast_correct
        rows.append(
            {
                "horizon": horizon,
                "current_states": current_states,
                "current_bits": current_bits,
                "exact_histories": exact_histories,
                "all_as_of_required_bits": ceil_log2(exact_histories),
                "max_all_as_of_fast_correct_with_current_bits": fast_correct,
                "minimum_all_as_of_fallback_fraction": forced_fallback
                / exact_histories,
            }
        )

    assert rows[2]["current_states"] == 228
    assert rows[3]["current_states"] == 579
    assert rows[3]["exact_histories"] == 20_736
    assert rows[3]["current_bits"] == 10
    assert rows[3]["max_all_as_of_fast_correct_with_current_bits"] == 1_024
    # Polynomial current state divided by exponential history count tends to 0.
    assert all(
        left["minimum_all_as_of_fallback_fraction"]
        < right["minimum_all_as_of_fallback_fraction"]
        for left, right in zip(rows[2:], rows[3:])
    )
    return rows


def main() -> int:
    assignments = verify_exhaustive_transcript_core()
    rows = versioned_boundary_rows()

    print("Certificate archive-access transcript bound")
    print()
    print(f"  [ok] exhaustive transcript assignments: {assignments:,}")
    print(
        "  [ok] exact deterministic bound: b + t*w >= "
        "ceil(log2(N - fallback - error))"
    )
    print()
    print(
        f"{'n':>2} {'current':>9} {'b':>3} {'histories':>12} "
        f"{'all-as-of b':>11} {'forced fallback':>16}"
    )
    for row in rows:
        print(
            f"{row['horizon']:2d} {row['current_states']:9d} "
            f"{row['current_bits']:3d} {row['exact_histories']:12d} "
            f"{row['all_as_of_required_bits']:11d} "
            f"{row['minimum_all_as_of_fallback_fraction']:15.6f}"
        )
    print()
    print(
        "Conclusion: active state, archive cells read, and accepted output "
        "capacity are separate bottlenecks. A current-frontier-sized fast path "
        "cannot answer a history-identifying all-as-of contract on more than "
        "an exponentially vanishing fraction of histories without archive work."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
