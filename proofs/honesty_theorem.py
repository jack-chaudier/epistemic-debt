#!/usr/bin/env python3
"""Honesty Theorem exact check: full witnesses vs cheaper honest certificates.

The theory document's Honesty Theorem has a load-bearing semantic fork:

1. Exact-witness honesty: the system may answer only when it can recover the
   exact witness object. This is the semantics already used by the vendored
   `breach` frontier.
2. Certificate honesty: the system may answer when it can give at least one
   valid certificate for the answer. For the Q_(k,p) families, any surviving
   protected witness certifies `feasible`; for causal_referee the recorded
   witness is a whole adjustment set, so certificate honesty remains exact-set
   honesty unless alternative adjustment sets are modeled.

This script exhaustively searches partitions of the vendored exact frontier
row spaces. Exit code 0 iff the exact-witness theorem holds on all checked
models and the certificate variant exposes the expected cheaper intermediate
quotient on the Q families.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))
import exact_pareto_frontier as epf
from phase_transition_sweep import Output


@dataclass(frozen=True)
class HonestySummary:
    label: str
    answer_states: int
    exact_witness_states: int
    certificate_states: int
    joint_states: int

    @property
    def exact_witness_extra_bits(self) -> float:
        return math.log2(self.exact_witness_states / self.answer_states)

    @property
    def certificate_extra_bits(self) -> float:
        return math.log2(self.certificate_states / self.answer_states)

    @property
    def certificate_savings_bits(self) -> float:
        return math.log2(self.joint_states / self.certificate_states)


def frontier_models() -> tuple[epf.FrontierModel, ...]:
    return (
        epf.build_probe_joint_model(3, 2),
        epf.build_probe_joint_model(4, 2),
        epf.build_probe_joint_model(5, 3),
        epf.build_dataset_support_model(epf.build_causal_referee_spec()),
    )


def answer_quotient_size(model: epf.FrontierModel) -> int:
    return len({tuple(output.answer for output in row) for row in model.rows})


def joint_quotient_size(model: epf.FrontierModel) -> int:
    return len({tuple((output.answer, output.witness) for output in row) for row in model.rows})


def exact_witness_block(model: epf.FrontierModel, mask: int) -> bool:
    indices = tuple(index for index in range(len(model.rows)) if mask & (1 << index))
    for probe_index in range(len(model.rows[0])):
        if len({model.rows[index][probe_index] for index in indices}) != 1:
            return False
    return True


def certificates(model: epf.FrontierModel, output: Output) -> frozenset[tuple[int, ...]]:
    if model.label.startswith("Q_(") and output.answer == "feasible":
        return frozenset((witness,) for witness in output.witness)
    return frozenset((output.witness,))


def certificate_block(model: epf.FrontierModel, mask: int) -> bool:
    indices = tuple(index for index in range(len(model.rows)) if mask & (1 << index))
    for probe_index in range(len(model.rows[0])):
        outputs = tuple(model.rows[index][probe_index] for index in indices)
        if len({output.answer for output in outputs}) != 1:
            return False
        common = set(certificates(model, outputs[0]))
        for output in outputs[1:]:
            common &= certificates(model, output)
        if not common:
            return False
    return True


def minimal_partition(
    model: epf.FrontierModel,
    block_ok: Callable[[epf.FrontierModel, int], bool],
) -> tuple[int, ...]:
    state_count = len(model.rows)
    full_mask = (1 << state_count) - 1
    valid_by_anchor: list[list[int]] = [[] for _ in range(state_count)]
    for mask in range(1, 1 << state_count):
        if block_ok(model, mask):
            anchor = (mask & -mask).bit_length() - 1
            valid_by_anchor[anchor].append(mask)

    @lru_cache(maxsize=None)
    def solve(mask: int) -> tuple[int, ...]:
        if mask == 0:
            return ()
        anchor = (mask & -mask).bit_length() - 1
        best: tuple[int, ...] | None = None
        for block in valid_by_anchor[anchor]:
            if block & ~mask:
                continue
            candidate = (block,) + solve(mask ^ block)
            if best is None or (len(candidate), candidate) < (len(best), best):
                best = candidate
        assert best is not None
        return best

    return solve(full_mask)


def minimal_state_count(
    model: epf.FrontierModel,
    block_ok: Callable[[epf.FrontierModel, int], bool],
) -> int:
    return len(minimal_partition(model, block_ok))


def summarize_model(model: epf.FrontierModel) -> HonestySummary:
    return HonestySummary(
        label=model.label,
        answer_states=answer_quotient_size(model),
        exact_witness_states=minimal_state_count(model, exact_witness_block),
        certificate_states=minimal_state_count(model, certificate_block),
        joint_states=joint_quotient_size(model),
    )


def main() -> int:
    rows = tuple(summarize_model(model) for model in frontier_models())
    print(
        f"{'model':16}{'answer':>8}{'exact':>8}{'cert':>8}{'joint':>8}"
        f"{'exact bits':>12}{'cert bits':>11}{'cert saves':>12}"
    )
    for row in rows:
        print(
            f"{row.label:16}{row.answer_states:8}{row.exact_witness_states:8}"
            f"{row.certificate_states:8}{row.joint_states:8}"
            f"{row.exact_witness_extra_bits:12.3f}"
            f"{row.certificate_extra_bits:11.3f}"
            f"{row.certificate_savings_bits:12.3f}"
        )

    q_rows = [row for row in rows if row.label.startswith("Q_(")]
    causal = next(row for row in rows if row.label == "causal_referee")
    checks = [
        (
            "exact-witness honesty requires the full witness quotient",
            all(row.exact_witness_states == row.joint_states for row in rows),
        ),
        (
            "certificate honesty has a strict intermediate quotient on every Q family",
            all(row.answer_states < row.certificate_states < row.joint_states for row in q_rows),
        ),
        (
            "causal_referee has no certificate shortcut in this support model",
            causal.certificate_states == causal.joint_states,
        ),
    ]
    print()
    for name, passed in checks:
        print(f"  [{'ok' if passed else 'FAIL'}] {name}")

    if all(passed for _, passed in checks):
        print(
            "\nConclusion: EXACT on checked finite models: exact-witness honesty "
            "requires the full witness quotient, while one-certificate honesty "
            "has a cheaper intermediate quotient for Q_(k,p)."
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
