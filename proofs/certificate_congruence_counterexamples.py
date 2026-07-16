#!/usr/bin/env python3
"""Small exact counterexamples for certificate-compatible state aggregation.

The examples kill three tempting generalizations of E0:

1. minimum static common-certificate state need not be right-congruent at the
   same state count (a state-minimal three-element commutative monoid);
2. pairwise certificate compatibility is not transitive and cannot be closed
   into an equivalence relation; and
3. minimum right-congruent certificate machines need not be unique, and the
   admissible congruences need not have a join.
4. the gap between static and continuation-sufficient certificate state is
   unbounded, even for one unary update and one constant answer.
5. an overlapping closed cover projected from history fibers can use fewer
   states than every partition of pre-aggregated semantic states.

All models are fully explicit, stdlib-only, and exhaustively enumerate their
set partitions.  Exit code 0 iff the stated counterexamples reproduce.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, Iterator


if not __debug__:
    raise RuntimeError("exact theorem checks require Python assertions; do not use -O")


Partition = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class Contract:
    name: str
    states: tuple[str, ...]
    answers: tuple[str, ...]
    certificates: tuple[frozenset[str], ...]
    updates: tuple[tuple[int, ...], ...]
    update_names: tuple[str, ...]


def set_partitions(size: int) -> Iterator[Partition]:
    """Generate each unlabeled set partition once in restricted-growth order."""

    blocks: list[list[int]] = []

    def walk(element: int) -> Iterator[Partition]:
        if element == size:
            yield tuple(tuple(block) for block in blocks)
            return
        for block in blocks:
            block.append(element)
            yield from walk(element + 1)
            block.pop()
        blocks.append([element])
        yield from walk(element + 1)
        blocks.pop()

    yield from walk(0)


def block_static(contract: Contract, block: Iterable[int]) -> bool:
    members = tuple(block)
    if len({contract.answers[index] for index in members}) != 1:
        return False
    common = set(contract.certificates[members[0]])
    for index in members[1:]:
        common.intersection_update(contract.certificates[index])
    return bool(common)


def static_valid(contract: Contract, partition: Partition) -> bool:
    return all(block_static(contract, block) for block in partition)


def right_congruent(contract: Contract, partition: Partition) -> bool:
    owner = {
        state: block_index
        for block_index, block in enumerate(partition)
        for state in block
    }
    for block in partition:
        for update in contract.updates:
            if len({owner[update[state]] for state in block}) != 1:
                return False
    return True


def valid_partitions(contract: Contract) -> tuple[Partition, ...]:
    return tuple(
        partition
        for partition in set_partitions(len(contract.states))
        if static_valid(contract, partition)
    )


def minimum(partitions: Iterable[Partition]) -> tuple[Partition, ...]:
    partitions = tuple(partitions)
    size = min(map(len, partitions))
    return tuple(partition for partition in partitions if len(partition) == size)


def monoid_gap_contract() -> tuple[Contract, tuple[tuple[int, ...], ...]]:
    # e is the identity, a*a=z, and z is absorbing.  The table is symmetric.
    multiplication = (
        (0, 1, 2),
        (1, 2, 2),
        (2, 2, 2),
    )
    # Right multiplication by each monoid element supplies every continuation.
    updates = tuple(
        tuple(multiplication[state][right] for state in range(3))
        for right in range(3)
    )
    return (
        Contract(
            name="three_element_commutative_monoid_gap",
            states=("e", "a", "z"),
            answers=("ok", "ok", "ok"),
            certificates=(frozenset({"alpha"}), frozenset({"alpha"}), frozenset({"beta"})),
            updates=updates,
            update_names=("append_e", "append_a", "append_z"),
        ),
        multiplication,
    )


def verify_monoid_gap() -> dict[str, object]:
    contract, multiplication = monoid_gap_contract()
    # Exhaustive closure, identity, commutativity, and associativity.
    for left in range(3):
        assert multiplication[0][left] == multiplication[left][0] == left
        for right in range(3):
            assert multiplication[left][right] in range(3)
            assert multiplication[left][right] == multiplication[right][left]
            for third in range(3):
                assert (
                    multiplication[multiplication[left][right]][third]
                    == multiplication[left][multiplication[right][third]]
                )

    static = valid_partitions(contract)
    static_minima = minimum(static)
    online = tuple(partition for partition in static if right_congruent(contract, partition))
    online_minima = minimum(online)
    assert static_minima == (((0, 1), (2,)),)
    assert online_minima == (((0,), (1,), (2,)),)

    # State-minimality: a two-state contract can only have static minimum one
    # versus right minimum two.  But the one-block partition is automatically
    # stable under every transition, so no two-state gap can exist.
    assert all(
        right_congruent(
            Contract(
                name="two_state_shape",
                states=("x", "y"),
                answers=("ok", "ok"),
                certificates=(frozenset({"c"}), frozenset({"c"})),
                updates=(update,),
                update_names=("u",),
            ),
            ((0, 1),),
        )
        for update in ((0, 0), (0, 1), (1, 0), (1, 1))
    )

    return {
        "name": contract.name,
        "static_minimum_states": len(static_minima[0]),
        "right_minimum_states": len(online_minima[0]),
        "static_minimum": static_minima[0],
        "right_minimum": online_minima[0],
        "splitting_update": "append_a",
        "images_of_static_block": (1, 2),
        "state_minimal": True,
    }


def unary_chain_contract(state_count: int) -> Contract:
    """A length-n chain whose final state needs an incompatible certificate."""

    assert state_count >= 3
    successor = tuple(min(state + 1, state_count - 1) for state in range(state_count))
    return Contract(
        name=f"unary_chain_gap_{state_count}",
        states=tuple(f"s_{state}" for state in range(state_count)),
        answers=tuple("ok" for _ in range(state_count)),
        certificates=tuple(
            frozenset({"alpha"})
            if state < state_count - 1
            else frozenset({"beta"})
            for state in range(state_count)
        ),
        updates=(successor,),
        update_names=("advance",),
    )


def verify_unbounded_gap(max_states: int = 8) -> dict[str, object]:
    """Check the family static=2/right=n; the written argument handles all n."""

    checked: list[dict[str, int]] = []
    for state_count in range(3, max_states + 1):
        contract = unary_chain_contract(state_count)
        static = valid_partitions(contract)
        static_minima = minimum(static)
        online = tuple(
            partition for partition in static if right_congruent(contract, partition)
        )
        online_minima = minimum(online)
        expected_static = (
            tuple(range(state_count - 1)),
            (state_count - 1,),
        )
        expected_online = tuple((state,) for state in range(state_count))
        assert static_minima == (expected_static,)
        assert online_minima == (expected_online,)

        # General proof witness: if i < j < n-1 were merged, advancing
        # n-1-j times would send j to the beta state while i remains alpha.
        for left in range(state_count - 1):
            for right in range(left + 1, state_count - 1):
                steps = state_count - 1 - right
                assert right + steps == state_count - 1
                assert left + steps < state_count - 1

        checked.append(
            {
                "states": state_count,
                "static_minimum": len(static_minima[0]),
                "right_minimum": len(online_minima[0]),
            }
        )
    return {
        "name": "unbounded_unary_chain_gap",
        "checked_instances": checked,
        "all_n_at_least_3": {
            "static_minimum": 2,
            "right_minimum": "n",
            "proof": (
                "merging i<j<n-1 fails after n-1-j advances because j reaches "
                "the beta-only state while i remains alpha-only"
            ),
        },
    }


def verify_nontransitive_compatibility() -> dict[str, object]:
    nontransitive = (
        frozenset({"alpha"}),
        frozenset({"alpha", "beta"}),
        frozenset({"beta"}),
    )
    assert nontransitive[0] & nontransitive[1]
    assert nontransitive[1] & nontransitive[2]
    assert not nontransitive[0] & nontransitive[2]

    # A stronger obstruction: every pair overlaps, yet no certificate works
    # for the full block.  A compatibility graph would falsely accept it.
    certificates = (
        frozenset({"alpha", "beta"}),
        frozenset({"beta", "gamma"}),
        frozenset({"alpha", "gamma"}),
    )
    pairwise = {
        (left, right): bool(certificates[left] & certificates[right])
        for left in range(3)
        for right in range(left + 1, 3)
    }
    assert pairwise[(0, 1)]
    assert pairwise[(1, 2)]
    assert pairwise[(0, 2)]
    assert not set.intersection(*(set(value) for value in certificates))

    contract = Contract(
        name="nontransitive_pairwise_compatibility",
        states=("left", "bridge", "right"),
        answers=("ok", "ok", "ok"),
        certificates=certificates,
        updates=((0, 1, 2),),
        update_names=("identity",),
    )
    minima = minimum(valid_partitions(contract))
    assert set(minima) == {
        ((0, 1), (2,)),
        ((0, 2), (1,)),
        ((0,), (1, 2)),
    }
    return {
        "name": contract.name,
        "nontransitive_chain": [(0, 1), (1, 2)],
        "pairwise_compatible": [(0, 1), (0, 2), (1, 2)],
        "pairwise_incompatible": [],
        "global_intersection": [],
        "minimum_partitions": minima,
    }


def nonunique_contract() -> Contract:
    # From start e, inputs U/V/W choose one of three absorbing states.  The
    # ambiguous middle output can be determinized toward either neighbor.
    return Contract(
        name="nonunique_minimum_certificate_machine",
        states=("e", "u", "v", "w"),
        answers=("start", "done", "done", "done"),
        certificates=(
            frozenset({"z"}),
            frozenset({"alpha"}),
            frozenset({"alpha", "beta"}),
            frozenset({"beta"}),
        ),
        updates=(
            (1, 1, 2, 3),
            (2, 1, 2, 3),
            (3, 1, 2, 3),
        ),
        update_names=("U", "V", "W"),
    )


def partition_join(left: Partition, right: Partition, state_count: int) -> Partition:
    adjacency = [set([state]) for state in range(state_count)]
    for partition in (left, right):
        for block in partition:
            for state in block:
                adjacency[state].update(block)
    unseen = set(range(state_count))
    blocks: list[tuple[int, ...]] = []
    while unseen:
        root = min(unseen)
        component = {root}
        frontier = [root]
        while frontier:
            state = frontier.pop()
            for neighbor in adjacency[state] - component:
                component.add(neighbor)
                frontier.append(neighbor)
        unseen.difference_update(component)
        blocks.append(tuple(sorted(component)))
    return tuple(blocks)


def verify_nonunique_minima() -> dict[str, object]:
    contract = nonunique_contract()
    admissible = tuple(
        partition
        for partition in valid_partitions(contract)
        if right_congruent(contract, partition)
    )
    minima = minimum(admissible)
    expected = {((0,), (1, 2), (3,)), ((0,), (1,), (2, 3))}
    assert set(minima) == expected
    left, right = minima
    join = partition_join(left, right, len(contract.states))
    assert join == ((0,), (1, 2, 3))
    assert not static_valid(contract, join)
    return {
        "name": contract.name,
        "minimum_states": len(minima[0]),
        "minimum_partitions": minima,
        "join": join,
        "join_admissible": False,
        "consequence": "admissible congruences form a meet-semilattice, not necessarily a lattice",
    }


def verify_closed_cover_partition_gap() -> dict[str, object]:
    """Check the smallest projected-cover versus semantic-partition gap.

    State 1 accepts either certificate and can be reached with either of two
    implementation states.  The implementation fibers remain disjoint on
    actual input histories; only their projection onto semantic states overlaps.
    """

    contract = Contract(
        name="three_state_projected_closed_cover_gap",
        states=("0", "1", "2"),
        answers=("ok", "ok", "ok"),
        certificates=(
            frozenset({"alpha"}),
            frozenset({"alpha", "beta"}),
            frozenset({"beta"}),
        ),
        # x: 0->2, 1->1, 2->0; r sends every semantic state to 1.
        updates=((2, 1, 0), (1, 1, 1)),
        update_names=("x", "r"),
    )
    semantic_minima = minimum(
        partition
        for partition in valid_partitions(contract)
        if right_congruent(contract, partition)
    )
    assert semantic_minima == (((0,), (1,), (2,)),)

    cover: Partition = ((0, 1), (1, 2))
    cover_certificates = ("alpha", "beta")
    for block, cert in zip(cover, cover_certificates):
        assert all(cert in contract.certificates[state] for state in block)

    # x swaps the two cover blocks.  r maps both semantic images to {1},
    # which lies in either block; retaining the implementation state makes both
    # copies of semantic state 1 reachable and keeps the history machine exact.
    implementation_transitions = ((1, 0), (0, 1))
    for cover_state, block in enumerate(cover):
        for update_index, update in enumerate(contract.updates):
            target = implementation_transitions[update_index][cover_state]
            image = {update[state] for state in block}
            assert image <= set(cover[target])

    initial_pair = (0, 0)
    reachable = {initial_pair}
    frontier = [initial_pair]
    while frontier:
        semantic_state, cover_state = frontier.pop()
        for update_index, update in enumerate(contract.updates):
            pair = (
                update[semantic_state],
                implementation_transitions[update_index][cover_state],
            )
            assert pair[0] in cover[pair[1]]
            if pair not in reachable:
                reachable.add(pair)
                frontier.append(pair)
    assert reachable == {(0, 0), (2, 1), (1, 0), (1, 1)}

    # One implementation state is impossible because reachable semantic states
    # 0 and 2 have disjoint accepted certificate sets.
    assert not contract.certificates[0] & contract.certificates[2]
    return {
        "name": contract.name,
        "semantic_partition_minimum": len(semantic_minima[0]),
        "projected_closed_cover_minimum": len(cover),
        "cover": cover,
        "implementation_transitions": {
            name: implementation_transitions[index]
            for index, name in enumerate(contract.update_names)
        },
        "reachable_semantic_implementation_pairs": tuple(sorted(reachable)),
        "scope": (
            "history fibers partition histories; their projection onto a "
            "many-to-one semantic state may overlap"
        ),
    }


def main() -> int:
    gap = verify_monoid_gap()
    unbounded = verify_unbounded_gap()
    compatibility = verify_nontransitive_compatibility()
    nonunique = verify_nonunique_minima()
    cover_gap = verify_closed_cover_partition_gap()

    print("Certificate-congruence counterexamples")
    print()
    print(
        "  [ok] state-minimal static/right gap: "
        f"{gap['static_minimum_states']} -> {gap['right_minimum_states']} states"
    )
    last_chain = unbounded["checked_instances"][-1]
    print(
        "  [ok] unbounded unary-chain gap: static 2 -> right n "
        f"(exhaustive through n={last_chain['states']})"
    )
    print("  [ok] pairwise compatibility is nontransitive; global intersection fails")
    print(
        "  [ok] nonunique optimal right machines: "
        f"{len(nonunique['minimum_partitions'])} minima at {nonunique['minimum_states']} states"
    )
    print("  [ok] the join of those minima is not certificate-admissible")
    print(
        "  [ok] projected closed cover beats every semantic partition: "
        f"{cover_gap['projected_closed_cover_minimum']} < "
        f"{cover_gap['semantic_partition_minimum']} states"
    )
    print()
    print(
        "Conclusion: static certificate minimality can understate exact online "
        "state by an unbounded factor; minimum implementations need not be "
        "canonical; pairwise compatibility cannot replace the blockwise "
        "global-intersection condition; and history machines must be separated "
        "from partitions of pre-aggregated semantic states."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
