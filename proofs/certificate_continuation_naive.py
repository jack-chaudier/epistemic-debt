#!/usr/bin/env python3
"""Naive exact audit of certificate partitions under continuation.

This is deliberately independent of the optimized continuation checker and the
vendored quotient implementation.  It reimplements the raw ``Q_(k,p)`` state
space, concatenation law, and output semantics directly, then:

1. groups raw states by their complete answer/witness traces under every exact
   right continuation;
2. enumerates certificate-valid set partitions incrementally;
3. finds every minimum static certificate partition;
4. finds every minimum such partition that is also a right congruence; and
5. checks right and left continuation separately for the lexicographic and
   audit-reported partitions.

The important orientation is ``compose(left, right)``: rows are left history
states and columns are exact right continuations.  Right congruence therefore
supports appending an exact continuation.  Left congruence is a separate,
stronger requirement needed before these row classes can be treated as a
two-sided quotient for composing independently summarized chunks.

Exit code 0 iff the independently enumerated counts, masks, and continuation
properties match the pinned finite audit claims.  ``--json`` emits the compact
machine-comparison payload; the default output is a human summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from array import array
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Iterator, Sequence


BOT = -1
MODELS = ((3, 2), (4, 2), (5, 3))

# Masks reported by the clean-room audit, relative to the row order reproduced
# below.  They choose the lowest-numbered surviving witness as certificate.
REPORTED_MASKS = {
    (3, 2): (1, 2, 4, 8, 48, 64),
    (4, 2): (1, 2, 4, 8, 16, 96, 128),
    (5, 3): (1, 2, 4, 8, 16, 32, 960, 3072, 4096),
}

# The lexicographically minimum static partitions expected from the partition
# objective used by the current honesty checker.
EXPECTED_LEX_MASKS = {
    (3, 2): (1, 2, 4, 8, 48, 64),
    (4, 2): (1, 2, 4, 8, 16, 96, 128),
    (5, 3): (1, 2, 4, 8, 16, 32, 576, 2176, 5376),
}


State = tuple[int, tuple[int, ...]]
PartitionMasks = tuple[int, ...]


@dataclass(frozen=True)
class Output:
    answer: str
    witness: tuple[int, ...]


@dataclass(frozen=True)
class NaiveModel:
    k: int
    p: int
    states: tuple[State, ...]
    state_index: dict[State, int]
    rows: tuple[tuple[Output, ...], ...]
    row_members: tuple[tuple[int, ...], ...]
    representatives: tuple[int, ...]
    raw_to_row: tuple[int, ...]
    right_target_rows: tuple[array, ...]
    left_target_rows: tuple[array, ...]

    @property
    def label(self) -> str:
        return f"Q_({self.k},{self.p})"


def enumerate_states(k: int, p: int) -> tuple[State, ...]:
    return tuple(
        (depth, tuple(coords))
        for depth in range(k + 1)
        for coords in product(range(BOT, depth + 1), repeat=p)
    )


def shift_coord(left_depth: int, right_coord: int, k: int) -> int:
    if right_coord == BOT:
        return BOT
    return min(k, left_depth + right_coord)


def compose(left: State, right: State, k: int) -> State:
    left_depth, left_coords = left
    right_depth, right_coords = right
    return (
        min(k, left_depth + right_depth),
        tuple(
            max(left_coord, shift_coord(left_depth, right_coord, k))
            for left_coord, right_coord in zip(left_coords, right_coords)
        ),
    )


def output(state: State, k: int) -> Output:
    survivors = tuple(
        index + 1 for index, coord in enumerate(state[1]) if coord == k
    )
    return Output("feasible" if survivors else "blocked", survivors)


def certificates(value: Output) -> frozenset[int]:
    # Witness labels are 1..p.  Token 0 denotes the unique empty certificate
    # for a blocked output.
    if value.answer == "feasible":
        return frozenset(value.witness)
    return frozenset((0,))


def build_model(k: int, p: int) -> NaiveModel:
    states = enumerate_states(k, p)
    state_index = {state: index for index, state in enumerate(states)}

    raw_rows = tuple(
        tuple(output(compose(left, right, k), k) for right in states)
        for left in states
    )

    grouped: dict[tuple[Output, ...], list[int]] = {}
    for raw_index, row in enumerate(raw_rows):
        grouped.setdefault(row, []).append(raw_index)

    # Reproduce the current probe-model row order so the pinned integer masks
    # remain directly comparable.  Semantic row names are also emitted because
    # masks should not be treated as stable across a future ordering change.
    ordered = sorted(
        grouped.items(),
        key=lambda item: (str(item[0]), item[1][0]),
    )
    rows = tuple(row for row, _ in ordered)
    row_members = tuple(tuple(members) for _, members in ordered)
    representatives = tuple(members[0] for _, members in ordered)

    raw_to_row_list = [0] * len(states)
    for row_index, members in enumerate(row_members):
        for raw_index in members:
            raw_to_row_list[raw_index] = row_index
    raw_to_row = tuple(raw_to_row_list)

    # Compact byte tables keep the deliberately exhaustive raw-state checks
    # simple without turning Python integer-object overhead into the bottleneck.
    right_target_rows: list[array] = []
    left_target_rows: list[array] = []
    for state in states:
        right_target_rows.append(
            array(
                "B",
                (
                    raw_to_row[state_index[compose(state, continuation, k)]]
                    for continuation in states
                ),
            )
        )
        left_target_rows.append(
            array(
                "B",
                (
                    raw_to_row[state_index[compose(continuation, state, k)]]
                    for continuation in states
                ),
            )
        )

    return NaiveModel(
        k=k,
        p=p,
        states=states,
        state_index=state_index,
        rows=rows,
        row_members=row_members,
        representatives=representatives,
        raw_to_row=raw_to_row,
        right_target_rows=tuple(right_target_rows),
        left_target_rows=tuple(left_target_rows),
    )


def mask_for_block(block: Sequence[int]) -> int:
    mask = 0
    for row_index in block:
        mask |= 1 << row_index
    return mask


def canonical_masks(blocks: Sequence[Sequence[int]]) -> PartitionMasks:
    masks = [mask_for_block(block) for block in blocks]
    return tuple(sorted(masks, key=lambda mask: (mask & -mask).bit_length() - 1))


def block_map(masks: PartitionMasks, row_count: int) -> tuple[int, ...]:
    mapping = [-1] * row_count
    for block_index, mask in enumerate(masks):
        for row_index in range(row_count):
            if mask >> row_index & 1:
                if mapping[row_index] != -1:
                    raise AssertionError(f"row {row_index} appears in multiple blocks")
                mapping[row_index] = block_index
    if any(block_index == -1 for block_index in mapping):
        raise AssertionError("partition does not cover every row")
    return tuple(mapping)


def make_block_validator(model: NaiveModel):
    @lru_cache(maxsize=None)
    def valid(block: tuple[int, ...]) -> bool:
        if not block:
            return False
        for probe_index in range(len(model.states)):
            values = tuple(model.rows[row_index][probe_index] for row_index in block)
            if len({value.answer for value in values}) != 1:
                return False
            common = set(certificates(values[0]))
            for value in values[1:]:
                common.intersection_update(certificates(value))
            if not common:
                return False
        return True

    return valid


def iter_valid_partitions(model: NaiveModel) -> Iterator[tuple[tuple[int, ...], ...]]:
    """Generate every certificate-valid row partition incrementally.

    Blocks are created in first-element order, the standard restricted-growth
    representation of an unlabeled set partition.  Invalid partial blocks are
    pruned immediately.  No bitmask partition dynamic program is used.
    """

    block_valid = make_block_validator(model)
    blocks: list[list[int]] = []
    row_count = len(model.rows)

    def walk(row_index: int) -> Iterator[tuple[tuple[int, ...], ...]]:
        if row_index == row_count:
            yield tuple(tuple(block) for block in blocks)
            return

        for block_index in range(len(blocks)):
            blocks[block_index].append(row_index)
            candidate = tuple(blocks[block_index])
            if block_valid(candidate):
                yield from walk(row_index + 1)
            blocks[block_index].pop()

        blocks.append([row_index])
        yield from walk(row_index + 1)
        blocks.pop()

    yield from walk(0)


def state_json(state: State) -> list[object]:
    return [state[0], list(state[1])]


def smallest_congruence_counterexample(
    model: NaiveModel,
    masks: PartitionMasks,
    side: str,
) -> dict[str, object] | None:
    row_to_block = block_map(masks, len(model.rows))

    # Ordering is block, then semantic row, then raw enumeration index.  This
    # exposes within-row left failures while retaining the row-6/row-9 right
    # counterexample as the first Q_(5,3) lex-partition failure.
    raw_by_block: list[list[int]] = [[] for _ in masks]
    for raw_index in sorted(
        range(len(model.states)),
        key=lambda index: (model.raw_to_row[index], index),
    ):
        raw_by_block[row_to_block[model.raw_to_row[raw_index]]].append(raw_index)

    target_rows = (
        model.right_target_rows if side == "right" else model.left_target_rows
    )

    for block_index, members in enumerate(raw_by_block):
        if len(members) < 2:
            continue
        first = members[0]
        first_signature = bytes(
            row_to_block[row_index] for row_index in target_rows[first]
        )
        for second in members[1:]:
            second_signature = bytes(
                row_to_block[row_index] for row_index in target_rows[second]
            )
            if first_signature == second_signature:
                continue
            continuation_index = next(
                index
                for index, (left_block, right_block) in enumerate(
                    zip(first_signature, second_signature)
                )
                if left_block != right_block
            )
            continuation = model.states[continuation_index]
            first_state = model.states[first]
            second_state = model.states[second]
            if side == "right":
                first_image = compose(first_state, continuation, model.k)
                second_image = compose(second_state, continuation, model.k)
            else:
                first_image = compose(continuation, first_state, model.k)
                second_image = compose(continuation, second_state, model.k)
            first_image_raw = model.state_index[first_image]
            second_image_raw = model.state_index[second_image]
            return {
                "side": side,
                "block": block_index,
                "state_a_raw": first,
                "state_b_raw": second,
                "state_a_row": model.raw_to_row[first],
                "state_b_row": model.raw_to_row[second],
                "state_a": state_json(first_state),
                "state_b": state_json(second_state),
                "continuation_raw": continuation_index,
                "continuation": state_json(continuation),
                "image_a": state_json(first_image),
                "image_b": state_json(second_image),
                "image_a_row": model.raw_to_row[first_image_raw],
                "image_b_row": model.raw_to_row[second_image_raw],
                "image_a_block": first_signature[continuation_index],
                "image_b_block": second_signature[continuation_index],
            }
    return None


def is_congruence(model: NaiveModel, masks: PartitionMasks, side: str) -> bool:
    return smallest_congruence_counterexample(model, masks, side) is None


def semantic_row_payload(model: NaiveModel, row_index: int) -> dict[str, object]:
    representative_raw = model.representatives[row_index]
    representative = model.states[representative_raw]
    survivors = list(output(representative, model.k).witness)
    if survivors:
        name = "F_{" + ",".join(str(value) for value in survivors) + "}"
        kind = "feasible_survivors"
    else:
        name = f"B_{representative[0]}"
        kind = "blocked_depth"
    return {
        "index": row_index,
        "mask": 1 << row_index,
        "name": name,
        "kind": kind,
        "depth": representative[0],
        "survivors": survivors,
        "weight": len(model.row_members[row_index]),
        "representative_raw": representative_raw,
        "representative": state_json(representative),
    }


def analyze_model(k: int, p: int) -> dict[str, object]:
    model = build_model(k, p)

    valid_by_size: dict[int, set[PartitionMasks]] = {}
    for blocks in iter_valid_partitions(model):
        masks = canonical_masks(blocks)
        valid_by_size.setdefault(len(masks), set()).add(masks)

    static_minimum = min(valid_by_size)
    static_masks = tuple(sorted(valid_by_size[static_minimum]))
    lex_masks = min(static_masks)
    reported_masks = REPORTED_MASKS[(k, p)]

    right_minimum = -1
    right_masks: tuple[PartitionMasks, ...] = ()
    for size in sorted(valid_by_size):
        candidates = tuple(
            masks
            for masks in sorted(valid_by_size[size])
            if is_congruence(model, masks, "right")
        )
        if candidates:
            right_minimum = size
            right_masks = candidates
            break

    if right_minimum < 0:
        raise AssertionError(f"{model.label}: no right-congruent partition found")

    lex_right_counterexample = smallest_congruence_counterexample(
        model, lex_masks, "right"
    )
    lex_left_counterexample = smallest_congruence_counterexample(
        model, lex_masks, "left"
    )
    reported_right_counterexample = smallest_congruence_counterexample(
        model, reported_masks, "right"
    )
    reported_left_counterexample = smallest_congruence_counterexample(
        model, reported_masks, "left"
    )

    answer_count = len(
        {
            tuple(value.answer for value in row)
            for row in model.rows
        }
    )

    payload: dict[str, object] = {
        "label": model.label,
        "counts": {
            "raw": len(model.states),
            "rows": len(model.rows),
            "answers": answer_count,
        },
        "rows": [
            semantic_row_payload(model, row_index)
            for row_index in range(len(model.rows))
        ],
        "static": {
            "minimum": static_minimum,
            "minimum_masks": [list(masks) for masks in static_masks],
        },
        "right": {
            "minimum": right_minimum,
            "minimum_masks": [list(masks) for masks in right_masks],
        },
        "lex": {
            "masks": list(lex_masks),
            "right": lex_right_counterexample is None,
            "left": lex_left_counterexample is None,
        },
        "reported": {
            "masks": list(reported_masks),
            "right": reported_right_counterexample is None,
            "left": reported_left_counterexample is None,
        },
        "counterexamples": {
            "lex_right": lex_right_counterexample,
            "reported_left": reported_left_counterexample,
        },
    }

    expected_counts = {
        (3, 2): (54, 7, 5, 6),
        (4, 2): (90, 8, 6, 7),
        (5, 3): (783, 13, 7, 9),
    }[(k, p)]
    observed_counts = (
        len(model.states),
        len(model.rows),
        answer_count,
        static_minimum,
    )
    if observed_counts != expected_counts:
        raise AssertionError(
            f"{model.label}: counts {observed_counts} != {expected_counts}"
        )
    if lex_masks != EXPECTED_LEX_MASKS[(k, p)]:
        raise AssertionError(
            f"{model.label}: lex masks {lex_masks} != "
            f"{EXPECTED_LEX_MASKS[(k, p)]}"
        )
    if reported_masks not in static_masks:
        raise AssertionError(f"{model.label}: reported masks are not static-minimum")
    if reported_masks not in right_masks:
        raise AssertionError(f"{model.label}: reported masks are not right-minimum")
    expected_lex_right = (k, p) != (5, 3)
    if (lex_right_counterexample is None) != expected_lex_right:
        raise AssertionError(f"{model.label}: unexpected lex right-congruence result")
    if reported_right_counterexample is not None:
        raise AssertionError(f"{model.label}: reported partition fails on the right")
    if reported_left_counterexample is None:
        raise AssertionError(f"{model.label}: expected reported left failure")

    return payload


def build_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "mask_basis": "bit i denotes rows[i]",
        "models": [analyze_model(k, p) for k, p in MODELS],
    }


def render_human(payload: dict[str, object]) -> str:
    lines = [
        "Naive certificate-continuation audit",
        "(right = exact append; left = summarized right-operand compatibility)",
        "",
    ]
    for model in payload["models"]:
        counts = model["counts"]
        static = model["static"]
        right = model["right"]
        lex = model["lex"]
        reported = model["reported"]
        lines.append(
            f"{model['label']}: raw={counts['raw']} rows={counts['rows']} "
            f"answers={counts['answers']} static_min={static['minimum']} "
            f"right_min={right['minimum']}"
        )
        lines.append(
            f"  lex={tuple(lex['masks'])} right={lex['right']} left={lex['left']}"
        )
        lines.append(
            "  reported="
            f"{tuple(reported['masks'])} right={reported['right']} "
            f"left={reported['left']}"
        )
        lines.append(
            f"  static minima={len(static['minimum_masks'])}; "
            f"right minima={len(right['minimum_masks'])}"
        )
        counterexample = model["counterexamples"]["lex_right"]
        if counterexample is not None:
            lines.append(
                "  first lex-right failure: "
                f"rows {counterexample['state_a_row']}/{counterexample['state_b_row']} "
                f"+ {counterexample['continuation']} -> rows "
                f"{counterexample['image_a_row']}/{counterexample['image_b_row']}"
            )
        lines.append("")
    lines.append("All pinned finite checks passed.")
    return "\n".join(lines)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the compact machine-readable comparison payload",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    if args.json:
        json.dump(payload, sys.stdout, indent=2, sort_keys=False)
        sys.stdout.write("\n")
    else:
        print(render_human(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
