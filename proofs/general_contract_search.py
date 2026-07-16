#!/usr/bin/env python3
"""Canonical exact search for small query-and-justification contracts.

The framework makes the accepted-output relation explicit.  A contract state
may accept several complete outputs (answer plus certificate); an implementation
is sound only when every history represented by its visible state accepts the
emitted output.  The solver enumerates:

* answer and accepted-complete-output compatible partitions;
* minimum right-congruent partitions and, when a coherent left action is
  declared, minimum partitions stable on both sides;
* compatible and transition-closed accepted-output-labelled covers;
* canonical transition witnesses for every minimum closed cover.

For small fixtures, a second executable independently enumerates path-dependent
deterministic history machines and checks their reachable product with the
semantic system.  Agreement is required before the canonical report is emitted.
That independent agreement covers only the minimum closed-cover/history-machine
state count; partition minima, cover witnesses, and proof resources are not
claimed to be independently reproduced.
All arithmetic and output ordering are exact and deterministic.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence


ROOT = Path(__file__).resolve().parent
NAIVE = ROOT / "general_contract_search_naive.py"
RESULTS = ROOT / "general_contract_search_results.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class Output:
    id: str
    answer: str
    proof_size: int = 1


@dataclass(frozen=True)
class Contract:
    name: str
    states: tuple[str, ...]
    outputs: tuple[Output, ...]
    accepted_outputs: tuple[frozenset[str], ...]
    transitions: tuple[tuple[int, ...], ...]
    event_names: tuple[str, ...]
    start: int = 0
    left_transitions: tuple[tuple[int, ...], ...] = ()

    def validate(self) -> None:
        state_count = len(self.states)
        output_ids = {output.id for output in self.outputs}
        require(state_count > 0, f"{self.name}: empty state set")
        require(len(output_ids) == len(self.outputs), f"{self.name}: duplicate output")
        require(
            len(self.accepted_outputs) == state_count,
            f"{self.name}: acceptance arity",
        )
        for accepted in self.accepted_outputs:
            require(bool(accepted), f"{self.name}: empty acceptance fiber")
            require(accepted <= output_ids, f"{self.name}: unknown accepted output")
        require(
            len(self.transitions) == len(self.event_names),
            f"{self.name}: event arity",
        )
        require(
            len(set(self.event_names)) == len(self.event_names),
            f"{self.name}: duplicate event name",
        )
        for transition in self.transitions + self.left_transitions:
            require(len(transition) == state_count, f"{self.name}: transition arity")
            require(
                all(0 <= destination < state_count for destination in transition),
                f"{self.name}: transition outside state set",
            )
        require(0 <= self.start < state_count, f"{self.name}: invalid start")
        if self.left_transitions:
            require(
                len(self.left_transitions) == len(self.transitions),
                f"{self.name}: paired left/right event arity",
            )
            for left in self.left_transitions:
                for right in self.transitions:
                    require(
                        all(
                            left[right[state]] == right[left[state]]
                            for state in range(state_count)
                        ),
                        f"{self.name}: left/right actions do not commute",
                    )
            require(
                all(
                    left[self.start] == right[self.start]
                    for left, right in zip(
                        self.left_transitions, self.transitions, strict=True
                    )
                ),
                f"{self.name}: paired left/right generators disagree at start",
            )
        reached = {self.start}
        frontier = [self.start]
        while frontier:
            state = frontier.pop()
            for transition in self.transitions:
                destination = transition[state]
                if destination not in reached:
                    reached.add(destination)
                    frontier.append(destination)
        require(
            reached == set(range(state_count)),
            f"{self.name}: every declared state must be reachable from start",
        )

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "states": list(self.states),
            "outputs": [
                {
                    "id": output.id,
                    "answer": output.answer,
                    "proof_size": output.proof_size,
                }
                for output in self.outputs
            ],
            "accepted_outputs": [sorted(row) for row in self.accepted_outputs],
            "transitions": [list(row) for row in self.transitions],
            "event_names": list(self.event_names),
            "start": self.start,
            "left_transitions": [list(row) for row in self.left_transitions],
            "max_machine_states": len(self.states),
        }


def bits(mask: int) -> tuple[int, ...]:
    return tuple(index for index in range(mask.bit_length()) if mask & (1 << index))


def set_partitions(size: int) -> Iterator[tuple[int, ...]]:
    """Yield mask partitions in restricted-growth order."""

    blocks: list[int] = []

    def walk(element: int) -> Iterator[tuple[int, ...]]:
        if element == size:
            yield tuple(blocks)
            return
        bit = 1 << element
        for index in range(len(blocks)):
            blocks[index] |= bit
            yield from walk(element + 1)
            blocks[index] ^= bit
        blocks.append(bit)
        yield from walk(element + 1)
        blocks.pop()

    yield from walk(0)


def accepted_labels(contract: Contract, mode: str) -> tuple[frozenset[str], ...]:
    answer_by_output = {output.id: output.answer for output in contract.outputs}
    if mode == "proof":
        return contract.accepted_outputs
    require(mode == "answer", f"unknown compatibility mode: {mode}")
    return tuple(
        frozenset(answer_by_output[output] for output in accepted)
        for accepted in contract.accepted_outputs
    )


def common_labels(rows: Sequence[frozenset[str]], mask: int) -> tuple[str, ...]:
    members = bits(mask)
    common = set(rows[members[0]])
    for state in members[1:]:
        common.intersection_update(rows[state])
    return tuple(sorted(common))


def valid_blocks(contract: Contract, mode: str) -> dict[int, tuple[str, ...]]:
    rows = accepted_labels(contract, mode)
    result: dict[int, tuple[str, ...]] = {}
    for mask in range(1, 1 << len(contract.states)):
        common = common_labels(rows, mask)
        if common:
            result[mask] = common
    return result


def owner_map(partition: tuple[int, ...], state_count: int) -> tuple[int, ...]:
    owner = [-1] * state_count
    for block_index, mask in enumerate(partition):
        for state in bits(mask):
            require(owner[state] == -1, "partition blocks overlap")
            owner[state] = block_index
    require(all(index >= 0 for index in owner), "partition does not cover states")
    return tuple(owner)


def partition_closed(
    partition: tuple[int, ...],
    transitions: Sequence[Sequence[int]],
    state_count: int,
) -> bool:
    owner = owner_map(partition, state_count)
    for mask in partition:
        members = bits(mask)
        for transition in transitions:
            if len({owner[transition[state]] for state in members}) != 1:
                return False
    return True


def minimum_partitions(
    contract: Contract,
    mode: str,
    closure: str,
) -> tuple[tuple[int, ...], ...]:
    allowed = valid_blocks(contract, mode)
    candidates: list[tuple[int, ...]] = []
    for partition in set_partitions(len(contract.states)):
        if not all(mask in allowed for mask in partition):
            continue
        right = partition_closed(partition, contract.transitions, len(contract.states))
        left = (
            partition_closed(partition, contract.left_transitions, len(contract.states))
            if contract.left_transitions
            else True
        )
        if closure == "static" or (closure == "right" and right) or (
            closure == "two_sided" and right and left
        ):
            candidates.append(partition)
    require(bool(candidates), f"{contract.name}: no {closure} {mode} partition")
    minimum_size = min(map(len, candidates))
    return tuple(sorted(partition for partition in candidates if len(partition) == minimum_size))


def mask_image(mask: int, transition: Sequence[int]) -> int:
    image = 0
    for state in bits(mask):
        image |= 1 << transition[state]
    return image


def cover_witness(
    cover: tuple[int, ...],
    transitions: Sequence[Sequence[int]],
) -> tuple[tuple[int, ...], ...] | None:
    table: list[tuple[int, ...]] = []
    for transition in transitions:
        row: list[int] = []
        for mask in cover:
            image = mask_image(mask, transition)
            targets = [index for index, target in enumerate(cover) if image & ~target == 0]
            if not targets:
                return None
            row.append(min(targets))
        table.append(tuple(row))
    return tuple(table)


def minimum_covers(
    contract: Contract,
    mode: str,
    closed: bool,
) -> tuple[dict[str, object], ...]:
    allowed = valid_blocks(contract, mode)
    all_states = (1 << len(contract.states)) - 1
    masks = tuple(sorted(allowed))
    for size in range(1, len(contract.states) + 1):
        matches: list[dict[str, object]] = []
        for cover in itertools.combinations(masks, size):
            union = 0
            for mask in cover:
                union |= mask
            if union != all_states:
                continue
            witness = cover_witness(cover, contract.transitions) if closed else ()
            if closed and witness is None:
                continue
            matches.append(
                {
                    "blocks": [list(bits(mask)) for mask in cover],
                    "common_labels": [list(allowed[mask]) for mask in cover],
                    "transitions": (
                        {
                            event: list(witness[index])
                            for index, event in enumerate(contract.event_names)
                        }
                        if closed and witness is not None
                        else {}
                    ),
                }
            )
        if matches:
            matches.sort(key=canonical_json)
            return tuple(matches)
    raise RuntimeError(f"{contract.name}: failed to find a {mode} cover")


def partition_payload(partition: tuple[int, ...]) -> list[list[int]]:
    return [list(bits(mask)) for mask in partition]


def run_naive(contract: Contract) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(NAIVE)],
        input=canonical_json(contract.payload()),
        text=True,
        capture_output=True,
        check=False,
    )
    require(
        completed.returncode == 0,
        f"independent solver failed for {contract.name}: {completed.stderr}",
    )
    payload = json.loads(completed.stdout)
    require(isinstance(payload, dict), "independent solver returned non-object")
    return payload


def solve_contract(contract: Contract) -> dict[str, object]:
    contract.validate()
    modes: dict[str, object] = {}
    for mode in ("answer", "proof"):
        static = minimum_partitions(contract, mode, "static")
        right = minimum_partitions(contract, mode, "right")
        two_sided = (
            minimum_partitions(contract, mode, "two_sided")
            if contract.left_transitions
            else None
        )
        compatible_covers = minimum_covers(contract, mode, closed=False)
        closed_covers = minimum_covers(contract, mode, closed=True)
        modes[mode] = {
            "valid_block_count": len(valid_blocks(contract, mode)),
            "static_minimum_states": len(static[0]),
            "static_minima": [partition_payload(item) for item in static],
            "right_minimum_states": len(right[0]),
            "right_minima": [partition_payload(item) for item in right],
            "two_sided_status": (
                "APPLICABLE: stable under the declared commuting left/right actions"
                if two_sided is not None
                else "INAPPLICABLE: no left action declared"
            ),
            "two_sided_minimum_states": (
                len(two_sided[0]) if two_sided is not None else None
            ),
            "two_sided_minima": (
                [partition_payload(item) for item in two_sided]
                if two_sided is not None
                else []
            ),
            "compatible_cover_minimum_states": len(compatible_covers[0]["blocks"]),
            "compatible_cover_minima": list(compatible_covers),
            "closed_cover_minimum_states": len(closed_covers[0]["blocks"]),
            "closed_cover_minima": list(closed_covers),
        }
    independent = run_naive(contract)
    for mode in ("answer", "proof"):
        require(
            independent[mode]["minimum_states"]
            == modes[mode]["closed_cover_minimum_states"],
            f"{contract.name}: cover/machine disagreement in {mode} mode",
        )
    input_digest = hashlib.sha256(canonical_json(contract.payload()).encode()).hexdigest()
    return {
        "name": contract.name,
        "input_sha256": input_digest,
        "states": len(contract.states),
        "events": len(contract.event_names),
        "outputs": len(contract.outputs),
        "optimized": modes,
        "independent_machine_search": independent,
        "independent_crosscheck": {
            "status": "PASS",
            "crosschecked_fields": [
                "answer.closed_cover_minimum_states",
                "proof.closed_cover_minimum_states",
            ],
            "not_crosschecked": [
                "static/right/two-sided partition minima",
                "compatible-cover minima",
                "minimum-cover sets",
                "transition witnesses",
                "proof size or verifier resources",
            ],
        },
    }


def fixtures() -> tuple[Contract, ...]:
    cover_transitions = ((2, 1, 0), (1, 1, 1))
    cover_events = ("swap_ends", "reset_middle")
    shareable = Contract(
        name="shareable_proof_closed_cover",
        states=("left", "middle", "right"),
        outputs=(Output("alpha", "ok"), Output("beta", "ok")),
        accepted_outputs=(
            frozenset({"alpha"}),
            frozenset({"alpha", "beta"}),
            frozenset({"beta"}),
        ),
        transitions=cover_transitions,
        event_names=cover_events,
    )
    state_bound = Contract(
        name="state_bound_proof_erases_cover_gap",
        states=("left", "middle", "right"),
        outputs=(
            Output("alpha_at_left", "ok"),
            Output("alpha_at_middle", "ok"),
            Output("beta_at_middle", "ok"),
            Output("beta_at_right", "ok"),
        ),
        accepted_outputs=(
            frozenset({"alpha_at_left"}),
            frozenset({"alpha_at_middle", "beta_at_middle"}),
            frozenset({"beta_at_right"}),
        ),
        transitions=cover_transitions,
        event_names=cover_events,
    )
    multiplication = (
        (0, 1, 2),
        (1, 2, 2),
        (2, 2, 2),
    )
    monoid_transitions = tuple(
        tuple(multiplication[state][right] for state in range(3))
        for right in range(3)
    )
    monoid_gap = Contract(
        name="static_right_monoid_gap",
        states=("identity", "step", "absorbing"),
        outputs=(Output("alpha", "ok"), Output("beta", "ok")),
        accepted_outputs=(
            frozenset({"alpha"}),
            frozenset({"alpha"}),
            frozenset({"beta"}),
        ),
        transitions=monoid_transitions,
        event_names=("append_identity", "append_step", "append_absorbing"),
        left_transitions=monoid_transitions,
    )
    return shareable, state_bound, monoid_gap


def build_report() -> dict[str, object]:
    models = [solve_contract(contract) for contract in fixtures()]
    by_name = {model["name"]: model for model in models}
    shareable = by_name["shareable_proof_closed_cover"]["optimized"]["proof"]
    require(shareable["right_minimum_states"] == 3, "shareable partition minimum")
    require(shareable["closed_cover_minimum_states"] == 2, "shareable cover minimum")
    bound = by_name["state_bound_proof_erases_cover_gap"]["optimized"]["proof"]
    require(bound["closed_cover_minimum_states"] == 3, "state-bound proof minimum")
    monoid = by_name["static_right_monoid_gap"]["optimized"]["proof"]
    require(monoid["static_minimum_states"] == 2, "monoid static minimum")
    require(monoid["right_minimum_states"] == 3, "monoid right minimum")
    return {
        "schema_version": 1,
        "evidence_label": "EXACT",
        "scope": (
            "finite explicit accepted-output relations and transition systems; "
            "output identifiers are opaque labels, and proof-size, verifier-work, "
            "authentication, and archive-access realizability are outside this solver"
        ),
        "models": models,
        "verdicts": {
            "accepted_output_labelled_cover_advantage_exists": True,
            "state_bound_output_labels_can_erase_advantage": True,
            "static_compatibility_does_not_imply_online_stability": True,
        },
    }


def render(report: dict[str, object]) -> str:
    lines = ["General finite-contract exact search", ""]
    for model in report["models"]:
        proof = model["optimized"]["proof"]
        lines.append(
            "  [ok] "
            f"{model['name']}: static={proof['static_minimum_states']} "
            f"right={proof['right_minimum_states']} "
            f"closed-cover={proof['closed_cover_minimum_states']} "
            f"independent={model['independent_crosscheck']['status']}"
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    if "--write" in sys.argv:
        RESULTS.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
