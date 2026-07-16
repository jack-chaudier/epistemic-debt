#!/usr/bin/env python3
"""Independent exact sweep for the versioned-frontier checkpoint product law.

This checker deliberately ignores source names, proposition semantics, answers,
and the implementation in ``versioned_memory_contract.py``.  An event is only
``(cell, value)``.  A frontier records each cell's exact event count and latest
value.  For every checkpoint subset, the program compares exhaustive history
signatures with the claimed product of independent segment-summary counts.

Exit code 0 iff every finite check passes.  The proof and scope assumptions are
recorded in ``theory/certificate-continuation-research-ledger.md``.
"""
from __future__ import annotations

import itertools
import math
import sys
from collections.abc import Sequence


if not __debug__:
    raise RuntimeError("exact theorem checks require Python assertions; do not use -O")


Event = tuple[int, int]
History = tuple[Event, ...]
Frontier = tuple[tuple[int, int], ...]


def segment_count(length: int, cells: int, values: int) -> int:
    if length < 0 or cells < 1 or values < 1:
        raise ValueError("invalid segment parameters")
    if length == 0:
        return 1
    return sum(
        math.comb(cells, touched)
        * math.comb(length - 1, touched - 1)
        * values**touched
        for touched in range(1, min(cells, length) + 1)
    )


def checkpoint_count(boundaries: Sequence[int], cells: int, values: int) -> int:
    if tuple(boundaries) != tuple(sorted(set(boundaries))):
        raise ValueError("boundaries must be strictly increasing")
    if boundaries and boundaries[0] <= 0:
        raise ValueError("only positive boundaries need to be stored")
    prior = 0
    result = 1
    for boundary in boundaries:
        result *= segment_count(boundary - prior, cells, values)
        prior = boundary
    return result


def schedules(horizon: int) -> tuple[tuple[int, ...], ...]:
    if horizon == 0:
        return ((),)
    internal = tuple(range(1, horizon))
    return tuple(
        tuple(
            boundary
            for index, boundary in enumerate(internal)
            if mask & (1 << index)
        )
        + (horizon,)
        for mask in range(1 << len(internal))
    )


def frontier(history: History, cells: int) -> Frontier:
    counts = [0] * cells
    latest = [-1] * cells
    for cell, value in history:
        counts[cell] += 1
        latest[cell] = value
    return tuple(zip(counts, latest))


def checkpoint_signature(
    history: History, boundaries: Sequence[int], cells: int
) -> tuple[Frontier, ...]:
    return tuple(frontier(history[:boundary], cells) for boundary in boundaries)


def histories(cells: int, values: int, horizon: int) -> tuple[History, ...]:
    alphabet = tuple(itertools.product(range(cells), range(values)))
    return tuple(itertools.product(alphabet, repeat=horizon))


def verify_parameter_family(
    max_cells: int = 3,
    max_values: int = 3,
    max_horizon: int = 4,
) -> dict[str, int]:
    schedules_checked = 0
    histories_checked = 0
    for cells in range(1, max_cells + 1):
        for values in range(1, max_values + 1):
            for horizon in range(max_horizon + 1):
                words = histories(cells, values, horizon)
                histories_checked += len(words)
                for boundaries in schedules(horizon):
                    observed = len(
                        {
                            checkpoint_signature(word, boundaries, cells)
                            for word in words
                        }
                    )
                    assert observed == checkpoint_count(boundaries, cells, values)
                    schedules_checked += 1
    return {
        "histories_checked": histories_checked,
        "schedules_checked": schedules_checked,
    }


def verify_actual_contract_horizon_four() -> dict[tuple[int, ...], int]:
    cells = 4
    values = 3
    words = histories(cells, values, 4)
    observed = {
        boundaries: len(
            {checkpoint_signature(word, boundaries, cells) for word in words}
        )
        for boundaries in schedules(4)
    }
    expected_anchors = {
        (4,): 579,
        (1, 4): 2_736,
        (2, 4): 4_356,
        (1, 2, 4): 9_504,
        (1, 2, 3, 4): 20_736,
    }
    assert all(observed[key] == value for key, value in expected_anchors.items())
    assert all(observed[key] == checkpoint_count(key, cells, values) for key in observed)

    event_a = (0, 0)
    event_b = (1, 0)
    ab = (event_a, event_b)
    ba = (event_b, event_a)
    assert frontier(ab, cells) == frontier(ba, cells)
    assert checkpoint_signature(ab, (1,), cells) != checkpoint_signature(
        ba, (1,), cells
    )
    return observed


def main() -> int:
    generic = verify_parameter_family()
    actual = verify_actual_contract_horizon_four()
    print("Versioned-frontier checkpoint theorem checks")
    print()
    print(
        "  [ok] independent generic sweep: "
        f"{generic['histories_checked']:,} histories across "
        f"{generic['schedules_checked']:,} parameter/schedule cases"
    )
    print("  [ok] every m=4, v=3 checkpoint schedule through horizon 4")
    print("  [ok] product anchors:")
    for boundaries in ((4,), (1, 4), (2, 4), (1, 2, 4), (1, 2, 3, 4)):
        print(f"       {boundaries}: {actual[boundaries]:,}")
    print("  [ok] AB/BA current merge and retroactive-boundary separation")
    print()
    print(
        "Conclusion: ex ante complete-frontier checkpoint states factor by "
        "segment. Sparse temporal obligations can remain sublinear, but an "
        "unrestricted retrospective boundary family distinguishes every history."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
