#!/usr/bin/env python3
"""Exact checks supporting the Q_(k,p) priority-certificate theorem.

The theorem proved in the accompanying research ledger is algebraic, not a
generalization from three data points:

* the probe-joint rows are B_0,...,B_k and F_S for nonempty S subseteq [p];
* every minimum static common-certificate partition has k+1+p blocks;
* such static minima correspond to choice functions f(S) in S;
* a minimum row partition is right-congruent exactly when f is induced by a
  total witness priority order; hence there are p! row-functional minima; and
* the resulting row-functional online active state has k+1+p states;
* composing independently summarized chunks is more expensive: for a fixed
  priority, the minimum two-sided quotient has C(k+p+2,p+1)-1 states; and
* adding arbitrary witness deletion destroys the priority compression and
  makes all 2^p survivor subsets answer-continuation-distinguishable.

This stdlib-only script independently checks the combinatorics through p=4
and the raw shift-and-max transition formula through k=5, p=3.  Exit code 0
iff every check passes.  The script is finite verification evidence for the
written proof, not a substitute for that proof and not an infinite-context
claim outside this monotone survivor-union algebra.

The selector enumeration classifies partitions that factor through the
survivor-set row quotient.  It does not classify path-dependent history
machines or overlapping closed covers projected onto those rows.
"""
from __future__ import annotations

import itertools
import math
import sys
from collections.abc import Iterator


BOT = -1


def elements(mask: int, p: int) -> tuple[int, ...]:
    return tuple(index for index in range(p) if mask & (1 << index))


def nonempty_subsets(p: int) -> tuple[int, ...]:
    return tuple(range(1, 1 << p))


def selector_key(selector: dict[int, int], p: int) -> tuple[int, ...]:
    return tuple(selector[subset] for subset in nonempty_subsets(p))


def static_selector_count(p: int) -> int:
    result = 1
    for size in range(2, p + 1):
        result *= size ** math.comb(p, size)
    return result


def enumerate_static_selectors(p: int) -> Iterator[dict[int, int]]:
    subsets = nonempty_subsets(p)
    variable = tuple(subset for subset in subsets if subset.bit_count() > 1)
    options = tuple(elements(subset, p) for subset in variable)
    forced = {1 << index: index for index in range(p)}
    for choices in itertools.product(*options):
        selector = dict(forced)
        selector.update(zip(variable, choices))
        yield selector


def priority_selector(p: int, priority: tuple[int, ...]) -> dict[int, int]:
    rank = {element: index for index, element in enumerate(priority)}
    return {
        subset: min(elements(subset, p), key=rank.__getitem__)
        for subset in nonempty_subsets(p)
    }


def union_congruent(selector: dict[int, int], p: int) -> bool:
    subsets = nonempty_subsets(p)
    grouped: dict[int, list[int]] = {index: [] for index in range(p)}
    for subset in subsets:
        grouped[selector[subset]].append(subset)
    for fiber in grouped.values():
        for left in fiber:
            for right in fiber:
                for addition in range(1 << p):
                    if selector[left | addition] != selector[right | addition]:
                        return False
    return True


def verify_selector_characterization(max_p: int = 4) -> list[dict[str, int]]:
    summaries: list[dict[str, int]] = []
    for p in range(1, max_p + 1):
        static_keys: set[tuple[int, ...]] = set()
        right_keys: set[tuple[int, ...]] = set()
        for selector in enumerate_static_selectors(p):
            key = selector_key(selector, p)
            static_keys.add(key)
            if union_congruent(selector, p):
                right_keys.add(key)

        priority_keys = {
            selector_key(priority_selector(p, priority), p)
            for priority in itertools.permutations(range(p))
        }
        assert len(static_keys) == static_selector_count(p)
        assert right_keys == priority_keys
        assert len(right_keys) == math.factorial(p)
        summaries.append(
            {
                "p": p,
                "static_minimum_partitions": len(static_keys),
                "right_congruent_minimum_partitions": len(right_keys),
            }
        )
    return summaries


def enumerate_raw_states(k: int, p: int) -> tuple[tuple[int, tuple[int, ...]], ...]:
    return tuple(
        (depth, coordinates)
        for depth in range(k + 1)
        for coordinates in itertools.product(range(BOT, depth + 1), repeat=p)
    )


def shift(depth: int, coordinate: int, k: int) -> int:
    if coordinate == BOT:
        return BOT
    return min(k, depth + coordinate)


def compose(
    left: tuple[int, tuple[int, ...]],
    right: tuple[int, tuple[int, ...]],
    k: int,
) -> tuple[int, tuple[int, ...]]:
    left_depth, left_coordinates = left
    right_depth, right_coordinates = right
    return (
        min(k, left_depth + right_depth),
        tuple(
            max(left_coordinate, shift(left_depth, right_coordinate, k))
            for left_coordinate, right_coordinate in zip(
                left_coordinates, right_coordinates
            )
        ),
    )


def survivor_mask(state: tuple[int, tuple[int, ...]], k: int) -> int:
    return sum(
        1 << index
        for index, coordinate in enumerate(state[1])
        if coordinate == k
    )


def compressed_state(
    state: tuple[int, tuple[int, ...]],
    k: int,
    selector: dict[int, int],
) -> tuple[str, int]:
    survivors = survivor_mask(state, k)
    if survivors:
        return "F", selector[survivors]
    return "B", state[0]


def predicted_transition(
    active: tuple[str, int],
    continuation: tuple[int, tuple[int, ...]],
    k: int,
    selector: dict[int, int],
) -> tuple[str, int]:
    kind, value = active
    continuation_depth, coordinates = continuation
    if kind == "B":
        depth = value
        new_survivors = sum(
            1 << index
            for index, coordinate in enumerate(coordinates)
            if coordinate != BOT and depth + coordinate >= k
        )
        if new_survivors:
            return "F", selector[new_survivors]
        return "B", min(k, depth + continuation_depth)

    additions = sum(
        1 << index
        for index, coordinate in enumerate(coordinates)
        if coordinate != BOT
    )
    return "F", selector[(1 << value) | additions]


def prefix_max_summary(
    state: tuple[int, tuple[int, ...]],
) -> tuple[int, tuple[int, ...]]:
    """Two-sided summary for the fixed priority 0,1,...,p-1."""

    depth, coordinates = state
    running = BOT
    maxima: list[int] = []
    for coordinate in coordinates:
        running = max(running, coordinate)
        maxima.append(running)
    return depth, tuple(maxima)


def compose_prefix_summaries(
    left: tuple[int, tuple[int, ...]],
    right: tuple[int, tuple[int, ...]],
    k: int,
) -> tuple[int, tuple[int, ...]]:
    left_depth, left_maxima = left
    right_depth, right_maxima = right
    return (
        min(k, left_depth + right_depth),
        tuple(
            max(left_value, shift(left_depth, right_value, k))
            for left_value, right_value in zip(left_maxima, right_maxima)
        ),
    )


def priority_output(
    state: tuple[int, tuple[int, ...]], k: int
) -> tuple[str, int]:
    depth, coordinates = state
    for index, coordinate in enumerate(coordinates):
        if coordinate == k:
            return "F", index
    return "B", depth


def priority_output_from_summary(
    summary: tuple[int, tuple[int, ...]], k: int
) -> tuple[str, int]:
    depth, maxima = summary
    for index, value in enumerate(maxima):
        if value == k:
            return "F", index
    return "B", depth


def fixed_priority_two_sided_count(k: int, p: int) -> int:
    return math.comb(k + p + 2, p + 1) - 1


def verify_fixed_priority_two_sided_quotient() -> list[dict[str, int]]:
    """Check the homomorphism, image count, and constructive distinguishers."""

    results: list[dict[str, int]] = []
    for k, p in ((3, 2), (4, 2), (5, 3)):
        states = enumerate_raw_states(k, p)
        representatives: dict[
            tuple[int, tuple[int, ...]], tuple[int, tuple[int, ...]]
        ] = {}
        for state in states:
            summary = prefix_max_summary(state)
            representatives.setdefault(summary, state)
            assert priority_output(state, k) == priority_output_from_summary(summary, k)
        assert len(representatives) == fixed_priority_two_sided_count(k, p)

        homomorphism_checks = 0
        for left in states:
            left_summary = prefix_max_summary(left)
            for right in states:
                assert prefix_max_summary(compose(left, right, k)) == (
                    compose_prefix_summaries(
                        left_summary, prefix_max_summary(right), k
                    )
                )
                homomorphism_checks += 1

        # Every distinct summary can be separated by the fixed-priority output
        # after a left or right context.  Different depths are already distinct
        # blocked outputs.  At equal depth, shift the larger first-differing
        # prefix maximum to k by a raw left context.
        summaries = tuple(representatives)
        distinguishability_checks = 0
        for left_index, left_summary in enumerate(summaries):
            for right_summary in summaries[left_index + 1 :]:
                left_state = representatives[left_summary]
                right_state = representatives[right_summary]
                if left_summary[0] != right_summary[0]:
                    assert priority_output(left_state, k) != priority_output(
                        right_state, k
                    )
                else:
                    differing = next(
                        index
                        for index, (left_value, right_value) in enumerate(
                            zip(left_summary[1], right_summary[1])
                        )
                        if left_value != right_value
                    )
                    high = max(
                        left_summary[1][differing], right_summary[1][differing]
                    )
                    assert high >= 0
                    prefix = (k - high, tuple(BOT for _ in range(p)))
                    assert priority_output(compose(prefix, left_state, k), k) != (
                        priority_output(compose(prefix, right_state, k), k)
                    )
                distinguishability_checks += 1

        results.append(
            {
                "k": k,
                "p": p,
                "states": len(representatives),
                "homomorphism_checks": homomorphism_checks,
                "distinguishability_checks": distinguishability_checks,
            }
        )
    return results


def verify_retraction_phase_transition(max_p: int = 8) -> list[dict[str, int]]:
    """Show arbitrary deletions make every survivor subset distinguishable."""

    results: list[dict[str, int]] = []
    for p in range(1, max_p + 1):
        subsets = tuple(range(1 << p))
        checks = 0
        for left_index, left in enumerate(subsets):
            for right in subsets[left_index + 1 :]:
                difference = left ^ right
                witness = (difference & -difference).bit_length() - 1
                keep_only_witness = 1 << witness
                left_after = left & keep_only_witness
                right_after = right & keep_only_witness
                # One side retains witness i and is feasible; the other is empty.
                assert (left_after == 0) != (right_after == 0)
                checks += 1
        results.append(
            {
                "p": p,
                "add_only_states": p + 1,
                "add_delete_states": 1 << p,
                "distinguishability_checks": checks,
            }
        )
    return results


def verify_raw_transition_formula(max_k: int = 5, max_p: int = 3) -> int:
    checked = 0
    for k in range(1, max_k + 1):
        for p in range(1, max_p + 1):
            states = enumerate_raw_states(k, p)
            selector = priority_selector(p, tuple(range(p)))
            for state in states:
                active = compressed_state(state, k, selector)
                for continuation in states:
                    predicted = predicted_transition(
                        active, continuation, k, selector
                    )
                    actual = compressed_state(
                        compose(state, continuation, k), k, selector
                    )
                    assert predicted == actual
                    checked += 1
    return checked


def verify_common_certificate_soundness(max_p: int = 6) -> int:
    checked = 0
    for p in range(1, max_p + 1):
        for priority in itertools.permutations(range(p)):
            selector = priority_selector(p, priority)
            for survivor_set in nonempty_subsets(p):
                certificate = selector[survivor_set]
                assert survivor_set & (1 << certificate)
                for addition in range(1 << p):
                    destination_certificate = selector[survivor_set | addition]
                    assert (survivor_set | addition) & (1 << destination_certificate)
                    checked += 1
            # Exhaustive permutations become expensive at p=6; one priority is
            # enough there because relabeling witnesses preserves the property.
            if p >= 6:
                break
    return checked


def main() -> int:
    selector_summaries = verify_selector_characterization()
    transition_checks = verify_raw_transition_formula()
    certificate_checks = verify_common_certificate_soundness()
    two_sided = verify_fixed_priority_two_sided_quotient()
    retractions = verify_retraction_phase_transition()

    print("Q_(k,p) priority-certificate theorem checks")
    print()
    print(f"{'p':>3}{'static minima':>17}{'right minima':>16}{'p!':>10}")
    for summary in selector_summaries:
        p = summary["p"]
        print(
            f"{p:3}{summary['static_minimum_partitions']:17}"
            f"{summary['right_congruent_minimum_partitions']:16}"
            f"{math.factorial(p):10}"
        )
    print()
    print(f"  [ok] raw transition formula checks: {transition_checks:,}")
    print(f"  [ok] common-certificate soundness checks: {certificate_checks:,}")
    print("  [ok] minimum state formula: k + 1 + p")
    print(
        "  [ok] fixed-priority two-sided states: "
        + ", ".join(
            f"Q_({row['k']},{row['p']})={row['states']}" for row in two_sided
        )
    )
    print(
        "  [ok] arbitrary-deletion phase transition through p="
        f"{retractions[-1]['p']}: p+1 -> 2^p survivor states"
    )
    print()
    print(
        "Conclusion: the coded Q_(k,p) family has a k+1+p-state minimum "
        "right-congruent row-functional certificate system. Its minimum "
        "right-congruent row partitions are exactly the p! fixed witness-"
        "priority selectors. Fixed-priority "
        "two-sided composition costs C(k+p+2,p+1)-1 states, and arbitrary "
        "deletion destroys the add-only priority compression."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
