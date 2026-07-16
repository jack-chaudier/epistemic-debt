#!/usr/bin/env python3
"""Exact phase and refinement laws for binary linear justification contracts.

At horizon ``n`` a history is ``x in GF(2)^n``.  A declared contract is a
binary matrix ``A`` whose unique complete output is ``A x``.  This family is
restricted, but it includes point checkpoints, prefix parities, interval and
window parities, causal incidence rows, and monotone additions of such queries.

Two theorem statements are checked by exhaustive enumeration independently of
Gaussian elimination for every pair of row sets through n=3:

1. the exact quotient has ``2^rank(A)`` states (rank active bits);
2. extending A by B splits every old fiber into exactly
   ``2^(rank([A;B]) - rank(A))`` new fibers.

Consequently, when the retained old state is exactly `A x` with no auxiliary
slack, an extension is archive-dormant exactly when every new row is in the old
row span.  For an arbitrary retained state, dormancy is instead ordinary view
determinacy relative to that actual state.  Otherwise, for a deterministic zero-error refinement with
``c`` newly retained bits and at most ``t`` archive probes of ``w`` bits each,
``c + t w`` is at least the rank increment.  This is a linear-family theorem,
not a claimed characterization of arbitrary nonlinear contracts.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Iterable, Sequence


RESULTS = Path(__file__).with_name("linear_obligation_rank_results.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def parity(value: int) -> int:
    return value.bit_count() & 1


def signature(rows: Sequence[int], history: int) -> tuple[int, ...]:
    return tuple(parity(row & history) for row in rows)


def gf2_rank(rows: Iterable[int], width: int) -> int:
    """Row rank over GF(2), using an integer bit-vector elimination."""

    basis: dict[int, int] = {}
    for raw in rows:
        value = int(raw)
        require(0 <= value < 1 << width, "row outside declared width")
        while value:
            pivot = value.bit_length() - 1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def exhaustive_signature_count(rows: Sequence[int], width: int) -> int:
    return len({signature(rows, history) for history in range(1 << width)})


def exhaustive_extension_splits(
    old_rows: Sequence[int],
    new_rows: Sequence[int],
    width: int,
) -> tuple[int, ...]:
    old_fibers: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    for history in range(1 << width):
        old = signature(old_rows, history)
        new = signature(new_rows, history)
        old_fibers.setdefault(old, set()).add(new)
    return tuple(sorted(len(images) for images in old_fibers.values()))


def exhaustive_crosscheck(max_width: int = 3) -> dict[str, int]:
    matrix_pairs = 0
    histories_checked = 0
    for width in range(1, max_width + 1):
        possible_rows = tuple(range(1, 1 << width))
        row_sets = tuple(
            tuple(row for index, row in enumerate(possible_rows) if mask & (1 << index))
            for mask in range(1 << len(possible_rows))
        )
        for old_rows in row_sets:
            old_rank = gf2_rank(old_rows, width)
            require(
                exhaustive_signature_count(old_rows, width) == 1 << old_rank,
                "rank/signature-count disagreement",
            )
            for new_rows in row_sets:
                combined_rank = gf2_rank(old_rows + new_rows, width)
                increment = combined_rank - old_rank
                splits = exhaustive_extension_splits(old_rows, new_rows, width)
                require(
                    set(splits) == {1 << increment},
                    "rank-increment/fiber-split disagreement",
                )
                dormant_by_rank = increment == 0
                dormant_by_enumeration = set(splits) == {1}
                require(
                    dormant_by_rank == dormant_by_enumeration,
                    "archive-dormancy criterion disagreement",
                )
                matrix_pairs += 1
                histories_checked += 1 << width
    return {
        "maximum_width": max_width,
        "matrix_pairs": matrix_pairs,
        "history_pair_checks": histories_checked,
    }


def point_rows(width: int, positions: Iterable[int]) -> tuple[int, ...]:
    materialized = tuple(positions)
    require(
        all(0 <= position < width for position in materialized),
        "point outside horizon",
    )
    return tuple(1 << position for position in sorted(set(materialized)))


def prefix_rows(width: int, boundaries: Iterable[int]) -> tuple[int, ...]:
    rows: list[int] = []
    for boundary in sorted(set(boundaries)):
        require(1 <= boundary <= width, "prefix boundary outside horizon")
        rows.append((1 << boundary) - 1)
    return tuple(rows)


def interval_rows(width: int, intervals: Iterable[tuple[int, int]]) -> tuple[int, ...]:
    rows: list[int] = []
    for left, right in intervals:
        require(0 <= left < right <= width, "interval outside horizon")
        rows.append(((1 << (right - left)) - 1) << left)
    return tuple(rows)


def family_row(name: str, width: int) -> tuple[int, ...]:
    if name == "constant_global_parity":
        return ((1 << width) - 1,)
    if name == "logarithmic_power_of_two_points":
        return point_rows(width, (position for position in range(width) if position & (position + 1) == 0))
    if name == "sublinear_square_points":
        return point_rows(
            width,
            (root * root - 1 for root in range(1, math.isqrt(width) + 1)),
        )
    if name == "dense_fixed_windows_3":
        if width < 3:
            return ()
        return interval_rows(width, ((left, left + 3) for left in range(width - 2)))
    if name == "all_prefixes":
        return prefix_rows(width, range(1, width + 1))
    if name == "all_intervals":
        return interval_rows(
            width,
            ((left, right) for left in range(width) for right in range(left + 1, width + 1)),
        )
    if name == "identity_points":
        return point_rows(width, range(width))
    raise ValueError(name)


def phase_sweep(max_width: int = 16) -> list[dict[str, object]]:
    names = (
        "constant_global_parity",
        "logarithmic_power_of_two_points",
        "sublinear_square_points",
        "dense_fixed_windows_3",
        "all_prefixes",
        "all_intervals",
        "identity_points",
    )
    rows: list[dict[str, object]] = []
    for width in range(1, max_width + 1):
        families: dict[str, object] = {}
        for name in names:
            matrix = family_row(name, width)
            rank = gf2_rank(matrix, width)
            require(exhaustive_signature_count(matrix, width) == 1 << rank, name)
            families[name] = {
                "declared_rows": len(matrix),
                "rank_bits": rank,
                "quotient_states": 1 << rank,
            }
        rows.append({"horizon": width, "families": families})
    return rows


def extension_examples() -> list[dict[str, object]]:
    width = 8
    old = prefix_rows(width, (2, 4, 8))
    examples = (
        ("dependent_interval", interval_rows(width, ((2, 4),))),
        ("one_independent_point", point_rows(width, (0,))),
        ("three_independent_points", point_rows(width, (0, 2, 4))),
        ("identity_completion", point_rows(width, range(width))),
    )
    rows: list[dict[str, object]] = []
    for name, new in examples:
        old_rank = gf2_rank(old, width)
        combined_rank = gf2_rank(old + new, width)
        increment = combined_rank - old_rank
        splits = exhaustive_extension_splits(old, new, width)
        require(set(splits) == {1 << increment}, name)
        rows.append(
            {
                "name": name,
                "old_rank": old_rank,
                "new_declared_rows": len(new),
                "combined_rank": combined_rank,
                "rank_increment": increment,
                "new_fibers_per_old_fiber": 1 << increment,
                "archive_dormant": increment == 0,
                "zero_error_refinement_lower_bound_bits": increment,
            }
        )
    return rows


def build_report(max_width: int = 16) -> dict[str, object]:
    require(max_width >= 1, "max width must be positive")
    crosscheck = exhaustive_crosscheck()
    phases = phase_sweep(max_width)
    final = phases[-1]["families"]
    require(final["constant_global_parity"]["rank_bits"] == 1, "constant phase")
    require(
        final["dense_fixed_windows_3"]["rank_bits"] == max(0, max_width - 2),
        "fixed-window phase",
    )
    require(final["all_intervals"]["rank_bits"] == max_width, "interval identity")
    payload = {
        "schema_version": 1,
        "evidence_label": "THEOREM plus EXACT finite crosscheck",
        "scope": (
            "fixed-horizon binary linear unique-output contracts with the horizon "
            "supplied externally; an online family additionally needs compatible "
            "cross-horizon update maps"
        ),
        "theorems": {
            "phase_law": "active information bits equal rank(A_n)",
            "refinement_law": "new bits per old fiber equal rank([A;B])-rank(A)",
            "dormancy_criterion": (
                "starting from exactly retained state A*x and no auxiliary slack, "
                "archive can remain dormant iff row(B) is contained in row(A)"
            ),
            "resource_bound": "new_active_bits + probes * cell_bits >= rank increment",
        },
        "implementation_boundary": (
            "an implementation retaining a richer state C*x uses row(B) contained "
            "in row(C); the general criterion is factorization through actual state"
        ),
        "independent_crosscheck": crosscheck,
        "phase_sweep": phases,
        "extension_examples": extension_examples(),
        "boundary": (
            "rank is a complete classifier only for the declared linear family; arbitrary "
            "nonlinear accepted-output relations require continuation/cover complexity"
        ),
    }
    payload["canonical_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-width", type=int, default=16)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report(args.max_width)
    if args.write:
        RESULTS.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("Binary linear obligation rank law")
    print(
        "  [ok] exhaustive independent matrix-pair checks: "
        f"{report['independent_crosscheck']['matrix_pairs']:,}"
    )
    print(
        "  [ok] phase sweep through n="
        f"{args.max_width}: rank gives exact active bits"
    )
    for row in report["extension_examples"]:
        print(
            f"  [ok] {row['name']}: delta-rank={row['rank_increment']} "
            f"dormant={row['archive_dormant']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
