#!/usr/bin/env python3
"""Exact verifier-access obstruction for complete provenance certificates.

Fix a visible active state, a claimed output, a valid raw archive ``h``, and a
proof accepted on ``h`` by a perfectly sound deterministic verifier.  Every
same-visible-state archive ``h'`` that falsifies the output differs on a set of
cells Delta(h,h').  The probes on that accepting run must hit every such set;
otherwise the same proof and observations make the verifier accept ``h'``.

After restricting the raw-history domain to that fixed visible-state fiber,
minimizing over perfectly complete and perfectly sound proof systems with
unbounded proof and computation makes this hitting number exact: the proof
names a minimum cell set J, the verifier reads it, and exhaustive offline
checking confirms that the observed cylinder intersected with the fiber is
wholly inside the output-validity region.

Two structurally independent computations—difference-set transversals and
archive-cylinder containment—are exhaustively compared for every Boolean
validity relation through four archive cells.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


RESULTS = Path(__file__).with_name("certificate_verifier_hitting_results.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def agrees_on(left: int, right: int, cells: int) -> bool:
    return ((left ^ right) & cells) == 0


def minimum_hitting_certificate(
    history: int, valid_region: int, width: int
) -> tuple[int, int]:
    invalid = [
        other
        for other in range(1 << width)
        if not valid_region & (1 << other)
    ]
    differences = tuple(history ^ other for other in invalid)
    for size in range(width + 1):
        for cells in range(1 << width):
            if cells.bit_count() != size:
                continue
            if all(cells & difference for difference in differences):
                return size, cells
    raise RuntimeError("no hitting certificate")


def minimum_cylinder_certificate(
    history: int, valid_region: int, width: int
) -> tuple[int, int]:
    for size in range(width + 1):
        for cells in range(1 << width):
            if cells.bit_count() != size:
                continue
            cylinder_sound = all(
                valid_region & (1 << other)
                for other in range(1 << width)
                if agrees_on(history, other, cells)
            )
            if cylinder_sound:
                return size, cells
    raise RuntimeError("no sound cylinder")


def exhaustive_crosscheck(max_width: int = 4) -> dict[str, int]:
    relations = 0
    valid_history_checks = 0
    for width in range(1, max_width + 1):
        universe_size = 1 << width
        for valid_region in range(1, 1 << universe_size):
            relations += 1
            for history in range(universe_size):
                if not valid_region & (1 << history):
                    continue
                hitting = minimum_hitting_certificate(history, valid_region, width)
                cylinder = minimum_cylinder_certificate(history, valid_region, width)
                require(hitting[0] == cylinder[0], "hitting/cylinder disagreement")
                valid_history_checks += 1
    return {
        "maximum_width": max_width,
        "validity_relations": relations,
        "valid_history_checks": valid_history_checks,
    }


def negative_positive_rows(max_width: int = 10) -> list[dict[str, int]]:
    rows: list[dict[str, int]] = []
    for width in range(1, max_width + 1):
        zero_history = 0
        all_zero_valid = 1 << zero_history
        negative = minimum_hitting_certificate(zero_history, all_zero_valid, width)[0]
        positive_history = 1 << (width - 1)
        any_one_valid = ((1 << (1 << width)) - 1) ^ 1
        positive = minimum_hitting_certificate(
            positive_history, any_one_valid, width
        )[0]
        require(negative == width, "complete negative evidence should inspect every cell")
        require(positive == 1, "one positive witness cell should suffice")
        rows.append(
            {
                "archive_cells": width,
                "all_zero_complete_negative_probes": negative,
                "any_one_positive_witness_probes": positive,
            }
        )
    return rows


def build_report() -> dict[str, object]:
    report = {
        "schema_version": 1,
        "evidence_label": "THEOREM plus EXACT finite crosscheck",
        "scope": {
            "archive": "finite explicit raw cells restricted to one fixed visible-state fiber",
            "proof": "unbounded length and unbounded verifier computation",
            "soundness": "deterministic perfect soundness",
            "completeness": (
                "the lower bound conditions on an accepting proof; the exact "
                "minimum is over perfectly complete proof systems"
            ),
            "active_state": "fixed visible fiber; invalid alternatives share it",
            "contract_table": (
                "the finite validity relation and verifier description are nonuniform and uncharged"
            ),
        },
        "theorem": {
            "lower_bound": (
                "on every accepting valid run, verifier probes hit every "
                "same-state falsifying archive difference support"
            ),
            "exact_characterization": (
                "over perfectly complete/sound systems, minimum probes equal "
                "the minimum coordinates defining a sound archive cylinder "
                "within the fixed visible-state fiber"
            ),
        },
        "independent_crosscheck": exhaustive_crosscheck(),
        "positive_negative_separation": negative_positive_rows(),
        "boundary": (
            "randomized variants require proof-specific completeness/soundness quantifiers; "
            "binding authenticated summaries change the visible-state fiber and can remove "
            "the raw-cell alternatives; the n-probe negative example assumes every singleton "
            "flip remains in one fiber; cryptographic soundness is a different model"
        ),
        "novelty_boundary": (
            "the mathematical object is nondeterministic decision-tree certificate complexity; "
            "the provenance interpretation is specialized rather than foundational novelty"
        ),
    }
    report["canonical_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return report


def main() -> int:
    report = build_report()
    if "--write" in __import__("sys").argv:
        RESULTS.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("Certificate verifier counterexample-support hitting law")
    print(
        "  [ok] independent finite checks: "
        f"{report['independent_crosscheck']['valid_history_checks']:,}"
    )
    last = report["positive_negative_separation"][-1]
    print(
        f"  [ok] n={last['archive_cells']}: positive witness="
        f"{last['any_one_positive_witness_probes']} probe, complete negative="
        f"{last['all_zero_complete_negative_probes']} probes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
