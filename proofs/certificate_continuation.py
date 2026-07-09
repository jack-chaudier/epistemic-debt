#!/usr/bin/env python3
"""E0: exact continuation checks for common-certificate state systems.

This validator promotes the clean-room audit's provisional calculation into a
permanent, reproducible finite result.  It deliberately distinguishes three
objects that are easy to conflate:

* a static partition whose blocks have one sound certificate per query;
* a right-congruent partition, which defines a deterministic right action of
  the exact update semigroup on compact active states; and
* a two-sided congruence, which would additionally define a binary quotient
  semigroup on those compact states.

The checked Q_(k,p) models use the exact shift-and-max composition vendored in
``proofs/vendor/phase_transition_sweep.py``.  The atomic rows are the current
probe-joint observational quotient, not the full raw-state space.  All raw
states are nevertheless enumerated and used for continuation checks.

Exit code 0 iff every exact check passes and the deliberately independent
implementation in ``certificate_continuation_naive.py`` agrees on the frozen
agreement core.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


ROOT = Path(__file__).resolve().parent
VENDOR = ROOT / "vendor"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

import exact_pareto_frontier as epf  # noqa: E402
import phase_transition_sweep as pts  # noqa: E402


MODEL_PARAMETERS = ((3, 2), (4, 2), (5, 3))
REPORTED_PARTITIONS = {
    (3, 2): (1, 2, 4, 8, 48, 64),
    (4, 2): (1, 2, 4, 8, 16, 96, 128),
    (5, 3): (1, 2, 4, 8, 16, 32, 960, 3072, 4096),
}
RESULTS_PATH = ROOT / "certificate_continuation_e0_results.json"

RawState = tuple[int, tuple[int, ...]]
Partition = tuple[int, ...]
Certificate = tuple[int, ...]


@dataclass(frozen=True)
class ExactModel:
    k: int
    p: int
    label: str
    states: tuple[RawState, ...]
    outcomes: tuple[tuple[pts.Output, ...], ...]
    rows: tuple[tuple[pts.Output, ...], ...]
    row_members: tuple[tuple[int, ...], ...]
    raw_to_row: tuple[int, ...]
    state_to_index: dict[RawState, int]


@dataclass(frozen=True)
class ContinuationTables:
    # right[row][raw continuation] is a single destination row because the
    # probe-joint row equivalence is a right congruence.
    right: tuple[tuple[int, ...], ...]
    # left[row][raw continuation] is a bit-mask because one probe-joint row may
    # contain raw representatives separated by a left continuation.
    left: tuple[tuple[int, ...], ...]


def output_signature(row: Sequence[pts.Output]) -> tuple[tuple[str, tuple[int, ...]], ...]:
    return tuple((output.answer, output.witness) for output in row)


def build_model(k: int, p: int) -> ExactModel:
    spec = pts.build_compositional_spec_witness(k, p)
    frontier = epf.build_probe_joint_model(k, p)

    grouped: dict[tuple[tuple[str, tuple[int, ...]], ...], list[int]] = defaultdict(list)
    for raw_index, row in enumerate(spec.outcomes):
        grouped[output_signature(row)].append(raw_index)
    ordered_groups = sorted(grouped.items(), key=lambda item: (str(item[0]), item[1][0]))

    row_members = tuple(tuple(members) for _, members in ordered_groups)
    rows = tuple(tuple(spec.outcomes[members[0]]) for members in row_members)
    raw_to_row_list = [-1] * len(spec.states)
    for row_index, members in enumerate(row_members):
        for raw_index in members:
            raw_to_row_list[raw_index] = row_index

    # Reproduce the vendored aggregation exactly before building anything on it.
    assert rows == frontier.rows
    assert tuple(map(len, row_members)) == frontier.state_weights
    assert all(index >= 0 for index in raw_to_row_list)

    return ExactModel(
        k=k,
        p=p,
        label=spec.label,
        states=tuple(spec.states),
        outcomes=tuple(tuple(row) for row in spec.outcomes),
        rows=rows,
        row_members=row_members,
        raw_to_row=tuple(raw_to_row_list),
        state_to_index={state: index for index, state in enumerate(spec.states)},
    )


def state_payload(state: RawState) -> dict[str, object]:
    depth, coordinates = state
    return {"depth": depth, "coordinates": list(coordinates)}


def semantic_row_payload(model: ExactModel, row_index: int) -> dict[str, object]:
    members = model.row_members[row_index]
    depths = {model.states[raw_index][0] for raw_index in members}
    survivor_sets = {
        tuple(
            index + 1
            for index, coordinate in enumerate(model.states[raw_index][1])
            if coordinate == model.k
        )
        for raw_index in members
    }
    assert len(depths) == 1
    assert len(survivor_sets) == 1
    depth = next(iter(depths))
    survivors = next(iter(survivor_sets))
    if survivors:
        assert depth == model.k
        label = "F_{" + ",".join(map(str, survivors)) + "}"
        return {
            "kind": "feasible_survivor_set",
            "label": label,
            "depth": depth,
            "survivors": list(survivors),
        }
    return {
        "kind": "blocked_depth",
        "label": f"B_{depth}",
        "depth": depth,
        "survivors": [],
    }


def mask_members(mask: int, size: int) -> tuple[int, ...]:
    return tuple(index for index in range(size) if mask & (1 << index))


def block_map(partition: Partition, row_count: int) -> tuple[int, ...]:
    mapping = [-1] * row_count
    covered = 0
    for block_index, mask in enumerate(partition):
        assert mask and not (covered & mask)
        covered |= mask
        for row_index in mask_members(mask, row_count):
            mapping[row_index] = block_index
    assert covered == (1 << row_count) - 1
    return tuple(mapping)


def accepted_certificates(output: pts.Output) -> frozenset[Certificate]:
    if output.answer == "feasible":
        return frozenset((witness,) for witness in output.witness)
    return frozenset((output.witness,))


def common_output(
    model: ExactModel, mask: int, query_index: int
) -> tuple[str, tuple[Certificate, ...]] | None:
    rows = mask_members(mask, len(model.rows))
    outputs = tuple(model.rows[row][query_index] for row in rows)
    answers = {output.answer for output in outputs}
    if len(answers) != 1:
        return None
    common = set(accepted_certificates(outputs[0]))
    for output in outputs[1:]:
        common.intersection_update(accepted_certificates(output))
    if not common:
        return None
    return outputs[0].answer, tuple(sorted(common))


def certificate_block(model: ExactModel, mask: int) -> bool:
    return all(common_output(model, mask, query) is not None for query in range(len(model.states)))


def valid_certificate_blocks(model: ExactModel) -> tuple[int, ...]:
    return tuple(
        mask
        for mask in range(1, 1 << len(model.rows))
        if certificate_block(model, mask)
    )


def enumerate_partitions(row_count: int, valid_blocks: Sequence[int]) -> Iterator[Partition]:
    by_anchor: list[list[int]] = [[] for _ in range(row_count)]
    for mask in valid_blocks:
        anchor = (mask & -mask).bit_length() - 1
        by_anchor[anchor].append(mask)
    for blocks in by_anchor:
        blocks.sort()

    def walk(remaining: int, prefix: tuple[int, ...]) -> Iterator[Partition]:
        if not remaining:
            yield prefix
            return
        anchor = (remaining & -remaining).bit_length() - 1
        for block in by_anchor[anchor]:
            if not (block & ~remaining):
                yield from walk(remaining ^ block, prefix + (block,))

    yield from walk((1 << row_count) - 1, ())


def answer_partition(model: ExactModel) -> Partition:
    grouped: dict[tuple[str, ...], int] = defaultdict(int)
    for row_index, row in enumerate(model.rows):
        grouped[tuple(output.answer for output in row)] |= 1 << row_index
    return tuple(sorted(grouped.values(), key=lambda mask: (mask & -mask, mask)))


def exact_witness_partition(model: ExactModel) -> Partition:
    # Rows were constructed by unique full answer+witness traces.
    return tuple(1 << row_index for row_index in range(len(model.rows)))


def continuation_tables(model: ExactModel) -> ContinuationTables:
    right_rows: list[tuple[int, ...]] = []
    left_rows: list[tuple[int, ...]] = []
    for members in model.row_members:
        right_for_row: list[int] = []
        left_for_row: list[int] = []
        for continuation in model.states:
            right_destinations: set[int] = set()
            left_destinations: set[int] = set()
            for raw_index in members:
                state = model.states[raw_index]
                right_state = pts.compose_witness(state, continuation, model.k)
                left_state = pts.compose_witness(continuation, state, model.k)
                right_destinations.add(model.raw_to_row[model.state_to_index[right_state]])
                left_destinations.add(model.raw_to_row[model.state_to_index[left_state]])
            # Equality of complete right-output rows must itself be right stable.
            assert len(right_destinations) == 1
            right_for_row.append(next(iter(right_destinations)))
            left_for_row.append(sum(1 << row for row in left_destinations))
        right_rows.append(tuple(right_for_row))
        left_rows.append(tuple(left_for_row))
    return ContinuationTables(tuple(right_rows), tuple(left_rows))


def partition_failure(
    model: ExactModel,
    partition: Partition,
    tables: ContinuationTables,
    side: str,
) -> dict[str, object] | None:
    mapping = block_map(partition, len(model.rows))
    for source_block, mask in enumerate(partition):
        source_rows = mask_members(mask, len(model.rows))
        for continuation_index, continuation in enumerate(model.states):
            destination_blocks: set[int] = set()
            if side == "right":
                for source_row in source_rows:
                    destination_blocks.add(mapping[tables.right[source_row][continuation_index]])
            elif side == "left":
                for source_row in source_rows:
                    for destination_row in mask_members(
                        tables.left[source_row][continuation_index], len(model.rows)
                    ):
                        destination_blocks.add(mapping[destination_row])
            else:
                raise ValueError(f"unknown side: {side}")
            if len(destination_blocks) <= 1:
                continue

            witnesses: list[dict[str, object]] = []
            seen_destinations: set[int] = set()
            for source_row in source_rows:
                for raw_index in model.row_members[source_row]:
                    source_state = model.states[raw_index]
                    if side == "right":
                        destination_state = pts.compose_witness(
                            source_state, continuation, model.k
                        )
                    else:
                        destination_state = pts.compose_witness(
                            continuation, source_state, model.k
                        )
                    destination_raw = model.state_to_index[destination_state]
                    destination_row = model.raw_to_row[destination_raw]
                    destination_block = mapping[destination_row]
                    if destination_block in seen_destinations:
                        continue
                    seen_destinations.add(destination_block)
                    witnesses.append(
                        {
                            "source_row": source_row,
                            "source_raw_index": raw_index,
                            "source_state": state_payload(source_state),
                            "destination_row": destination_row,
                            "destination_block": destination_block,
                            "destination_state": state_payload(destination_state),
                        }
                    )
                    if len(seen_destinations) == len(destination_blocks):
                        break
                if len(seen_destinations) == len(destination_blocks):
                    break
            return {
                "side": side,
                "source_block": source_block,
                "source_block_mask": mask,
                "continuation_raw_index": continuation_index,
                "continuation_state": state_payload(continuation),
                "destination_blocks": sorted(destination_blocks),
                "witnesses": witnesses,
            }
    return None


def is_congruent(
    model: ExactModel,
    partition: Partition,
    tables: ContinuationTables,
    side: str,
) -> bool:
    return partition_failure(model, partition, tables, side) is None


def partition_payload(partition: Partition, row_count: int) -> dict[str, object]:
    return {
        "masks": list(partition),
        "blocks": [list(mask_members(mask, row_count)) for mask in partition],
    }


def verify_raw_closure(model: ExactModel) -> int:
    checked = 0
    for left in model.states:
        for right in model.states:
            assert pts.compose_witness(left, right, model.k) in model.state_to_index
            checked += 1
    return checked


def verify_scalar_associativity(k: int) -> int:
    # Composition is coordinatewise after the shared depth update, so checking
    # one coordinate for every valid depth/coordinate triple proves the tuple
    # operation associative for every p.
    scalar_states = tuple(
        (depth, coordinate)
        for depth in range(k + 1)
        for coordinate in range(pts.BOT, depth + 1)
    )
    checked = 0
    for left_depth, left_coordinate in scalar_states:
        for middle_depth, middle_coordinate in scalar_states:
            lm_depth = min(k, left_depth + middle_depth)
            lm_coordinate = max(
                left_coordinate,
                pts.shift_coord(left_depth, middle_coordinate, k),
            )
            for right_depth, right_coordinate in scalar_states:
                lhs_depth = min(k, lm_depth + right_depth)
                lhs_coordinate = max(
                    lm_coordinate,
                    pts.shift_coord(lm_depth, right_coordinate, k),
                )

                mr_depth = min(k, middle_depth + right_depth)
                mr_coordinate = max(
                    middle_coordinate,
                    pts.shift_coord(middle_depth, right_coordinate, k),
                )
                rhs_depth = min(k, left_depth + mr_depth)
                rhs_coordinate = max(
                    left_coordinate,
                    pts.shift_coord(left_depth, mr_coordinate, k),
                )
                assert (lhs_depth, lhs_coordinate) == (rhs_depth, rhs_coordinate)
                checked += 1
    return checked


def certificate_output_system(
    model: ExactModel, partition: Partition
) -> tuple[list[dict[str, object]], str, int]:
    records: list[tuple[tuple[str, tuple[Certificate, ...]], ...]] = []
    checked = 0
    for query_index in range(len(model.states)):
        profile: list[tuple[str, tuple[Certificate, ...]]] = []
        for mask in partition:
            result = common_output(model, mask, query_index)
            assert result is not None
            answer, certificates = result
            assert certificates
            # Recheck soundness against every represented row, not merely the
            # incremental intersection used to construct the set.
            for row_index in mask_members(mask, len(model.rows)):
                reference = model.rows[row_index][query_index]
                assert reference.answer == answer
                assert all(
                    certificate in accepted_certificates(reference)
                    for certificate in certificates
                )
                checked += 1
            profile.append((answer, certificates))
        records.append(tuple(profile))

    grouped: dict[tuple[tuple[str, tuple[Certificate, ...]], ...], list[int]] = defaultdict(list)
    for query_index, profile in enumerate(records):
        grouped[profile].append(query_index)

    profile_payloads: list[dict[str, object]] = []
    for profile_id, (profile, raw_indices) in enumerate(
        sorted(grouped.items(), key=lambda item: (str(item[0]), item[1][0]))
    ):
        profile_payloads.append(
            {
                "id": profile_id,
                "raw_query_indices": raw_indices,
                "outputs": [
                    {
                        "answer": answer,
                        "common_certificates": [list(certificate) for certificate in certificates],
                    }
                    for answer, certificates in profile
                ],
            }
        )

    canonical = json.dumps(profile_payloads, sort_keys=True, separators=(",", ":"))
    return profile_payloads, hashlib.sha256(canonical.encode()).hexdigest(), checked


def reachable_blocks(
    transitions: Sequence[Sequence[int]], initial: int, allowed_actions: Iterable[int]
) -> list[int]:
    allowed = tuple(sorted(set(allowed_actions)))
    reached = {initial}
    queue = deque([initial])
    while queue:
        state = queue.popleft()
        for action in allowed:
            destination = transitions[action][state]
            if destination not in reached:
                reached.add(destination)
                queue.append(destination)
    return sorted(reached)


def build_right_action(
    model: ExactModel,
    partition: Partition,
    tables: ContinuationTables,
) -> dict[str, object]:
    assert is_congruent(model, partition, tables, "right")
    mapping = block_map(partition, len(model.rows))

    raw_actions: list[tuple[int, ...]] = []
    for continuation_index in range(len(model.states)):
        transition: list[int] = []
        for mask in partition:
            source_rows = mask_members(mask, len(model.rows))
            destinations = {
                mapping[tables.right[row][continuation_index]] for row in source_rows
            }
            assert len(destinations) == 1
            transition.append(next(iter(destinations)))
        raw_actions.append(tuple(transition))

    grouped: dict[tuple[int, ...], list[int]] = defaultdict(list)
    for raw_index, action in enumerate(raw_actions):
        grouped[action].append(raw_index)
    ordered = sorted(grouped.items(), key=lambda item: (item[0], item[1][0]))
    raw_to_action = [-1] * len(model.states)
    classes: list[dict[str, object]] = []
    for action_id, (transition, members) in enumerate(ordered):
        for raw_index in members:
            raw_to_action[raw_index] = action_id
        classes.append(
            {
                "id": action_id,
                "transition": list(transition),
                "raw_state_indices": members,
            }
        )
    assert all(action >= 0 for action in raw_to_action)

    action_count = len(classes)
    composition: list[list[int]] = [[-1] * action_count for _ in range(action_count)]
    representative_checks = 0
    for left_action, left_class in enumerate(classes):
        for right_action, right_class in enumerate(classes):
            destinations: set[int] = set()
            for left_raw in left_class["raw_state_indices"]:
                for right_raw in right_class["raw_state_indices"]:
                    combined = pts.compose_witness(
                        model.states[left_raw], model.states[right_raw], model.k
                    )
                    combined_index = model.state_to_index[combined]
                    destinations.add(raw_to_action[combined_index])
                    representative_checks += 1
            assert len(destinations) == 1
            composition[left_action][right_action] = next(iter(destinations))

    # Explicitly verify the transformation action and associativity of the
    # induced continuation monoid.
    action_law_checks = 0
    for source in range(len(partition)):
        for left_action in range(action_count):
            after_left = classes[left_action]["transition"][source]
            for right_action in range(action_count):
                combined_action = composition[left_action][right_action]
                lhs = classes[right_action]["transition"][after_left]
                rhs = classes[combined_action]["transition"][source]
                assert lhs == rhs
                action_law_checks += 1

    associativity_checks = 0
    for first in range(action_count):
        for second in range(action_count):
            first_second = composition[first][second]
            for third in range(action_count):
                lhs = composition[first_second][third]
                rhs = composition[first][composition[second][third]]
                assert lhs == rhs
                associativity_checks += 1

    identity = (0, tuple(pts.BOT for _ in range(model.p)))
    identity_raw = model.state_to_index[identity]
    identity_action = raw_to_action[identity_raw]
    assert all(composition[identity_action][action] == action for action in range(action_count))
    assert all(composition[action][identity_action] == action for action in range(action_count))

    initial_row = model.raw_to_row[identity_raw]
    initial_block = mapping[initial_row]
    all_reached = reachable_blocks(
        [tuple(item["transition"]) for item in classes],
        initial_block,
        range(action_count),
    )
    unit_actions = {
        raw_to_action[index]
        for index, (depth, _) in enumerate(model.states)
        if depth == 1
    }
    unit_reached = reachable_blocks(
        [tuple(item["transition"]) for item in classes],
        initial_block,
        unit_actions,
    )

    composition_digest = hashlib.sha256(
        json.dumps(composition, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "active_state_count": len(partition),
        "action_class_count": action_count,
        "classes": classes,
        "raw_to_action": raw_to_action,
        "composition_table": composition,
        "composition_sha256": composition_digest,
        "identity_raw_index": identity_raw,
        "identity_action": identity_action,
        "initial_active_state": initial_block,
        "unit_depth_action_ids": sorted(unit_actions),
        "reachable_with_all_chunks": all_reached,
        "reachable_with_depth_one_events": unit_reached,
        "representative_pair_checks": representative_checks,
        "action_law_checks": action_law_checks,
        "associativity_checks": associativity_checks,
    }


def compact_failure(failure: dict[str, object] | None) -> object:
    if failure is None:
        return None
    return {
        "side": failure["side"],
        "source_block_mask": failure["source_block_mask"],
        "continuation_raw_index": failure["continuation_raw_index"],
        "destination_blocks": failure["destination_blocks"],
        "source_rows": [item["source_row"] for item in failure["witnesses"]],
    }


def model_report(model: ExactModel) -> dict[str, object]:
    row_count = len(model.rows)
    valid_blocks = valid_certificate_blocks(model)
    all_partitions = tuple(enumerate_partitions(row_count, valid_blocks))
    tables = continuation_tables(model)

    static_minimum = min(map(len, all_partitions))
    static_minimum_partitions = tuple(
        partition for partition in all_partitions if len(partition) == static_minimum
    )
    right_partitions = tuple(
        partition
        for partition in all_partitions
        if is_congruent(model, partition, tables, "right")
    )
    left_partitions = tuple(
        partition
        for partition in all_partitions
        if is_congruent(model, partition, tables, "left")
    )
    two_sided_partitions = tuple(
        partition for partition in right_partitions if partition in set(left_partitions)
    )
    right_minimum = min(map(len, right_partitions))
    right_minimum_partitions = tuple(
        partition for partition in right_partitions if len(partition) == right_minimum
    )

    reported = REPORTED_PARTITIONS[(model.k, model.p)]
    lexicographic = static_minimum_partitions[0]
    answer = answer_partition(model)
    exact = exact_witness_partition(model)

    assert len(answer) < static_minimum < len(exact)
    assert reported in right_minimum_partitions
    assert right_minimum == static_minimum
    assert all(certificate_block(model, mask) for mask in reported)

    reported_right_failure = partition_failure(model, reported, tables, "right")
    reported_left_failure = partition_failure(model, reported, tables, "left")
    lexicographic_right_failure = partition_failure(
        model, lexicographic, tables, "right"
    )
    lexicographic_left_failure = partition_failure(
        model, lexicographic, tables, "left"
    )
    full_witness_left_failure = partition_failure(model, exact, tables, "left")
    assert reported_right_failure is None
    assert reported_left_failure is not None
    if (model.k, model.p) == (5, 3):
        assert lexicographic_right_failure is not None
    else:
        assert lexicographic_right_failure is None
    assert full_witness_left_failure is not None

    output_profiles, output_digest, soundness_checks = certificate_output_system(
        model, reported
    )
    right_action = build_right_action(model, reported, tables)
    closure_checks = verify_raw_closure(model)
    scalar_associativity_checks = verify_scalar_associativity(model.k)

    counts_by_size = Counter(map(len, all_partitions))
    right_counts_by_size = Counter(map(len, right_partitions))
    left_counts_by_size = Counter(map(len, left_partitions))
    two_sided_counts_by_size = Counter(map(len, two_sided_partitions))

    raw_states = [state_payload(state) for state in model.states]
    rows = [
        {
            "row": row_index,
            "semantic_class": semantic_row_payload(model, row_index),
            "raw_state_indices": list(members),
            "weight": len(members),
        }
        for row_index, members in enumerate(model.row_members)
    ]

    report: dict[str, object] = {
        "label": model.label,
        "parameters": {"k": model.k, "p": model.p},
        "scope": "finite probe-joint observational quotient with all exact raw continuations",
        "counts": {
            "raw_states": len(model.states),
            "raw_queries": len(model.states),
            "probe_joint_rows": row_count,
            "answer_quotient_states": len(answer),
            "exact_witness_quotient_states": len(exact),
            "valid_certificate_blocks": len(valid_blocks),
            "certificate_partitions": len(all_partitions),
            "static_minimum_certificate_states": static_minimum,
            "static_minimum_partition_count": len(static_minimum_partitions),
            "right_minimum_certificate_states": right_minimum,
            "right_minimum_partition_count": len(right_minimum_partitions),
            "left_congruent_partition_count_on_probe_rows": len(left_partitions),
            "two_sided_partition_count_on_probe_rows": len(two_sided_partitions),
            "query_output_profiles": len(output_profiles),
        },
        "partition_counts_by_size": {
            "all_certificate": dict(sorted(counts_by_size.items())),
            "right_congruent": dict(sorted(right_counts_by_size.items())),
            "left_congruent": dict(sorted(left_counts_by_size.items())),
            "two_sided": dict(sorted(two_sided_counts_by_size.items())),
        },
        "partitions": {
            "answer": partition_payload(answer, row_count),
            "exact_witness": partition_payload(exact, row_count),
            "lexicographic_static_minimum": partition_payload(lexicographic, row_count),
            "reported_right_congruent_minimum": partition_payload(reported, row_count),
            "all_static_minima": [list(partition) for partition in static_minimum_partitions],
            "all_right_congruent_minima": [
                list(partition) for partition in right_minimum_partitions
            ],
        },
        "checks": {
            "reported_masks_reproduced": True,
            "reported_common_certificate_valid": True,
            "reported_answer_consistent": True,
            "reported_right_congruent": reported_right_failure is None,
            "reported_left_congruent": reported_left_failure is None,
            "reported_two_sided_congruent": (
                reported_right_failure is None and reported_left_failure is None
            ),
            "lexicographic_static_minimum_right_congruent": (
                lexicographic_right_failure is None
            ),
            "full_witness_rows_left_congruent": full_witness_left_failure is None,
            "raw_composition_closed": True,
            "raw_composition_associative": True,
            "right_action_closed": True,
            "right_action_associative": True,
            "certificate_output_sound": True,
            "all_active_states_reachable_with_all_chunks": (
                right_action["reachable_with_all_chunks"] == list(range(len(reported)))
            ),
            "all_active_states_reachable_with_depth_one_events": (
                right_action["reachable_with_depth_one_events"]
                == list(range(len(reported)))
            ),
        },
        "check_counts": {
            "raw_closure_pairs": closure_checks,
            "scalar_associativity_triples": scalar_associativity_checks,
            "certificate_row_query_checks": soundness_checks,
            "action_representative_pairs": right_action["representative_pair_checks"],
            "right_action_law_checks": right_action["action_law_checks"],
            "right_action_associativity_triples": right_action["associativity_checks"],
        },
        "counterexamples": {
            "lexicographic_static_minimum_right": lexicographic_right_failure,
            "lexicographic_static_minimum_left": lexicographic_left_failure,
            "reported_partition_left": reported_left_failure,
            "full_witness_row_partition_left": full_witness_left_failure,
        },
        "raw_states": raw_states,
        "probe_joint_rows": rows,
        "certificate_output_table": output_profiles,
        "certificate_output_sha256": output_digest,
        "right_action": right_action,
    }
    return report


def normalized_state(state: object) -> list[object]:
    """Normalize the two deliberately different implementations' state JSON."""

    if isinstance(state, dict):
        return [state["depth"], state["coordinates"]]
    assert isinstance(state, list) and len(state) == 2
    return state


def normalized_primary_failure(failure: dict[str, object] | None) -> object:
    if failure is None:
        return None
    witnesses = failure["witnesses"]
    assert len(witnesses) >= 2
    first, second = witnesses[:2]
    return {
        "side": failure["side"],
        "block": failure["source_block"],
        "state_a_raw": first["source_raw_index"],
        "state_b_raw": second["source_raw_index"],
        "state_a_row": first["source_row"],
        "state_b_row": second["source_row"],
        "state_a": normalized_state(first["source_state"]),
        "state_b": normalized_state(second["source_state"]),
        "continuation_raw": failure["continuation_raw_index"],
        "continuation": normalized_state(failure["continuation_state"]),
        "image_a": normalized_state(first["destination_state"]),
        "image_b": normalized_state(second["destination_state"]),
        "image_a_row": first["destination_row"],
        "image_b_row": second["destination_row"],
        "image_a_block": first["destination_block"],
        "image_b_block": second["destination_block"],
    }


def normalized_naive_failure(failure: dict[str, object] | None) -> object:
    if failure is None:
        return None
    keys = (
        "side",
        "block",
        "state_a_raw",
        "state_b_raw",
        "state_a_row",
        "state_b_row",
        "state_a",
        "state_b",
        "continuation_raw",
        "continuation",
        "image_a",
        "image_b",
        "image_a_row",
        "image_b_row",
        "image_a_block",
        "image_b_block",
    )
    return {key: failure[key] for key in keys}


def agreement_core(report: dict[str, object]) -> dict[str, object]:
    """Return facts independently computed by both implementations.

    The optimized checker also verifies the action law, action associativity,
    reachability, and output-table soundness.  Those stronger checks remain in
    the canonical report, but cannot honestly be called an independent
    reproduction because the deliberately simple checker does not implement
    them.  This core is restricted to the intersection of the two programs.
    """

    models: list[dict[str, object]] = []
    for model in report["models"]:
        counts = model["counts"]
        partitions = model["partitions"]
        checks = model["checks"]
        models.append(
            {
                "label": model["label"],
                "counts": {
                    "raw": counts["raw_states"],
                    "rows": counts["probe_joint_rows"],
                    "answers": counts["answer_quotient_states"],
                },
                "rows": [
                    {
                        "depth": row["semantic_class"]["depth"],
                        "survivors": row["semantic_class"]["survivors"],
                    }
                    for row in model["probe_joint_rows"]
                ],
                "static": {
                    "minimum": counts["static_minimum_certificate_states"],
                    "minimum_masks": partitions["all_static_minima"],
                },
                "right": {
                    "minimum": counts["right_minimum_certificate_states"],
                    "minimum_masks": partitions["all_right_congruent_minima"],
                },
                "lex": {
                    "masks": partitions["lexicographic_static_minimum"]["masks"],
                    "right": checks[
                        "lexicographic_static_minimum_right_congruent"
                    ],
                    "left": model["counterexamples"][
                        "lexicographic_static_minimum_left"
                    ]
                    is None,
                },
                "reported": {
                    "masks": partitions["reported_right_congruent_minimum"]["masks"],
                    "right": checks["reported_right_congruent"],
                    "left": checks["reported_left_congruent"],
                },
                "counterexamples": {
                    "lex_right": normalized_primary_failure(
                        model["counterexamples"][
                            "lexicographic_static_minimum_right"
                        ]
                    ),
                    "reported_left": normalized_primary_failure(
                        model["counterexamples"]["reported_partition_left"]
                    ),
                },
            }
        )
    return {"models": models}


def naive_agreement_core(payload: dict[str, object]) -> dict[str, object]:
    models: list[dict[str, object]] = []
    for model in payload["models"]:
        models.append(
            {
                "label": model["label"],
                "counts": model["counts"],
                "rows": [
                    {"depth": row["depth"], "survivors": row["survivors"]}
                    for row in model["rows"]
                ],
                "static": model["static"],
                "right": model["right"],
                "lex": model["lex"],
                "reported": model["reported"],
                "counterexamples": {
                    key: normalized_naive_failure(value)
                    for key, value in model["counterexamples"].items()
                },
            }
        )
    return {"models": models}


def core_digest(core: dict[str, object]) -> str:
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def independent_core() -> dict[str, object]:
    script = ROOT / "certificate_continuation_naive.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--json"],
        cwd=ROOT.parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return naive_agreement_core(json.loads(completed.stdout))


def build_report(compare_independent: bool = True) -> dict[str, object]:
    report: dict[str, object] = {
        "schema_version": 1,
        "evidence_label": "EXACT",
        "claim_scope": (
            "Finite Q_(3,2), Q_(4,2), and Q_(5,3) probe-joint models only; "
            "right-congruent active-state systems, not a universal infinite-context theorem."
        ),
        "models": [model_report(build_model(k, p)) for k, p in MODEL_PARAMETERS],
    }
    primary_core = agreement_core(report)
    digest = core_digest(primary_core)
    if compare_independent:
        naive_core = independent_core()
        assert naive_core == primary_core
        report["independent_reproduction"] = {
            "status": "PASS",
            "optimized_implementation": "proofs/certificate_continuation.py",
            "simple_implementation": "proofs/certificate_continuation_naive.py",
            "agreement_sha256": digest,
        }
    else:
        report["independent_reproduction"] = {
            "status": "SKIPPED",
            "agreement_sha256": digest,
        }
    return report


def render_summary(report: dict[str, object]) -> str:
    lines = [
        "E0 certificate-continuation exact validator",
        "",
        (
            f"{'model':10}{'raw':>7}{'rows':>7}{'answer':>9}{'static':>9}"
            f"{'right':>9}{'right opt':>11}{'left?':>8}{'actions':>9}"
        ),
    ]
    for model in report["models"]:
        counts = model["counts"]
        checks = model["checks"]
        lines.append(
            f"{model['label']:10}{counts['raw_states']:7}{counts['probe_joint_rows']:7}"
            f"{counts['answer_quotient_states']:9}"
            f"{counts['static_minimum_certificate_states']:9}"
            f"{counts['right_minimum_certificate_states']:9}"
            f"{counts['right_minimum_partition_count']:11}"
            f"{str(checks['reported_left_congruent']):>8}"
            f"{model['right_action']['action_class_count']:9}"
        )
        lex = checks["lexicographic_static_minimum_right_congruent"]
        lines.append(
            "  reported masks: "
            + str(tuple(model["partitions"]["reported_right_congruent_minimum"]["masks"]))
        )
        lines.append(
            f"  static optima={counts['static_minimum_partition_count']}; "
            f"right-congruent optima={counts['right_minimum_partition_count']}; "
            f"lexicographic optimum right-congruent={lex}"
        )
    lines.extend(
        [
            "",
            f"Independent reproduction: {report['independent_reproduction']['status']}",
            "Conclusion: EXACT on the checked finite models. The reported minimum common-",
            "certificate partitions are right congruences at no extra state count. They are",
            "not left congruences and therefore define right semigroup actions, not binary",
            "quotient semigroups. This is Level 1 evidence, not infinite context.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the full exact report")
    parser.add_argument(
        "--write-results",
        action="store_true",
        help=f"write the canonical report to {RESULTS_PATH.name}",
    )
    parser.add_argument(
        "--skip-independent",
        action="store_true",
        help="debug only: do not invoke the independent implementation",
    )
    args = parser.parse_args()

    report = build_report(compare_independent=not args.skip_independent)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write_results:
        RESULTS_PATH.write_text(rendered)
    if args.json:
        sys.stdout.write(rendered)
    else:
        print(render_summary(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
