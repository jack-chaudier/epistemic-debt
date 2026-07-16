#!/usr/bin/env python3
"""Independent brute-force history-machine solver for finite contracts.

This file intentionally does not import ``general_contract_search``.  It reads
one explicit contract from stdin and enumerates deterministic Moore machines in
BFS-canonical form.  Correctness is checked on the reachable product of the
semantic transition system and each candidate history machine.  Because one
semantic state may be paired with several machine states, this search includes
path-dependent implementations represented by overlapping closed covers.

The optimized solver enumerates blocks, partitions, and covers instead.  The
two programs share the serialized input relation and compare only their minimum
closed-cover/history-machine state counts.  Their stronger internal witnesses
and digests are not claimed to agree independently.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from collections import deque
from typing import Iterable


def fail(message: str) -> None:
    raise RuntimeError(message)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def accepted_labels(payload: dict[str, object], mode: str) -> tuple[tuple[str, ...], ...]:
    outputs = payload["outputs"]
    accepted = payload["accepted_outputs"]
    if not isinstance(outputs, list) or not isinstance(accepted, list):
        fail("invalid outputs or acceptance relation")
    answer_by_output = {
        str(item["id"]): str(item["answer"])
        for item in outputs
        if isinstance(item, dict)
    }
    rows: list[tuple[str, ...]] = []
    for row in accepted:
        if not isinstance(row, list):
            fail("acceptance rows must be lists")
        if mode == "proof":
            labels = {str(output) for output in row}
        elif mode == "answer":
            labels = {answer_by_output[str(output)] for output in row}
        else:
            fail(f"unknown mode: {mode}")
        if not labels:
            fail("every semantic state must accept at least one output")
        rows.append(tuple(sorted(labels)))
    return tuple(rows)


def transition_table(payload: dict[str, object]) -> tuple[tuple[int, ...], ...]:
    raw = payload["transitions"]
    if not isinstance(raw, list):
        fail("transitions must be a list")
    return tuple(tuple(int(destination) for destination in row) for row in raw)


def discovery_is_canonical(
    machine_transitions: tuple[tuple[int, ...], ...],
    event_count: int,
    state_count: int,
) -> bool:
    """Require first-discovery order 0,1,... to remove state renamings."""

    seen = {0}
    queue = deque([0])
    next_expected = 1
    while queue:
        state = queue.popleft()
        for event in range(event_count):
            destination = machine_transitions[event][state]
            if destination in seen:
                continue
            if destination != next_expected:
                return False
            seen.add(destination)
            queue.append(destination)
            next_expected += 1
    return len(seen) == state_count


def check_machine(
    semantic_transitions: tuple[tuple[int, ...], ...],
    accepted: tuple[tuple[str, ...], ...],
    start: int,
    machine_outputs: tuple[str, ...],
    machine_transitions: tuple[tuple[int, ...], ...],
) -> tuple[tuple[int, int], ...] | None:
    initial = (start, 0)
    reached = {initial}
    queue = deque([initial])
    while queue:
        semantic, machine = queue.popleft()
        if machine_outputs[machine] not in accepted[semantic]:
            return None
        for event, semantic_update in enumerate(semantic_transitions):
            pair = (
                semantic_update[semantic],
                machine_transitions[event][machine],
            )
            if pair not in reached:
                reached.add(pair)
                queue.append(pair)
    # The serialized fixtures promise that every semantic state is reachable.
    # Check that promise here instead of silently proving only a sub-contract.
    if {semantic for semantic, _ in reached} != set(range(len(accepted))):
        fail("contract contains semantic states unreachable from the declared start")
    return tuple(sorted(reached))


def machine_candidates(
    state_count: int,
    event_count: int,
    labels: Iterable[str],
):
    label_tuple = tuple(sorted(labels))
    for outputs in itertools.product(label_tuple, repeat=state_count):
        for flat in itertools.product(
            range(state_count), repeat=event_count * state_count
        ):
            transitions = tuple(
                tuple(flat[event * state_count : (event + 1) * state_count])
                for event in range(event_count)
            )
            if discovery_is_canonical(transitions, event_count, state_count):
                yield outputs, transitions


def solve(payload: dict[str, object], mode: str, max_states: int) -> dict[str, object]:
    accepted = accepted_labels(payload, mode)
    semantic_transitions = transition_table(payload)
    start = int(payload["start"])
    labels = sorted({label for row in accepted for label in row})
    checked = 0
    for state_count in range(1, max_states + 1):
        valid: list[dict[str, object]] = []
        for outputs, transitions in machine_candidates(
            state_count, len(semantic_transitions), labels
        ):
            checked += 1
            reached = check_machine(
                semantic_transitions,
                accepted,
                start,
                outputs,
                transitions,
            )
            if reached is None:
                continue
            valid.append(
                {
                    "outputs": list(outputs),
                    "transitions": [list(row) for row in transitions],
                    "reachable_product": [list(pair) for pair in reached],
                }
            )
        if valid:
            valid.sort(key=canonical_json)
            behavior_payload = {
                "mode": mode,
                "minimum_states": state_count,
                "machines": valid,
            }
            return {
                "mode": mode,
                "minimum_states": state_count,
                "minimum_machine_count": len(valid),
                "lexicographic_machine": valid[0],
                "behavior_sha256": hashlib.sha256(
                    canonical_json(behavior_payload).encode()
                ).hexdigest(),
                "candidates_checked": checked,
            }
    fail(f"no valid {mode} machine through {max_states} states")


def main() -> int:
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        fail("stdin must contain one contract object")
    max_states = int(payload.get("max_machine_states", len(payload["states"])))
    report = {
        "schema_version": 1,
        "contract": payload["name"],
        "answer": solve(payload, "answer", max_states),
        "proof": solve(payload, "proof", max_states),
    }
    print(canonical_json(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
