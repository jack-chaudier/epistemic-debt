#!/usr/bin/env python3
"""Exact evolving-contract checks for causal checkpoints and bounded retroactivity.

This module turns the static checkpoint product law into two explicit migration
algorithms:

* A checkpoint signaled exactly at its boundary by a fixed exogenous schedule
  freezes the incrementally maintained
  current segment summary.  It needs no archive read and produces exactly the
  same complete frontiers as an ex-ante checkpoint contract.
* A retained exact last-w window plus the complete frontier immediately before
  that window supports any newly declared boundary inside the window by replaying
  at most w active events.  A boundary before the window is not determined in
  general (the checked AB/BA witness survives with an identical suffix).

Events are immutable append-only ``(cell, value)`` publications; targeted
invalidation or retroactive mutation of an earlier frontier is outside this
model. The finite checks compare structurally different representations: independent
segment summaries versus direct prefix replay.  The written asymptotic theorem
for fixed cells/values is that r=o(n) checkpoints supplied by the fixed
exogenous schedule require O(r log(1+n/r))=o(n) active bits.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable, Sequence


Event = tuple[int, int]
History = tuple[Event, ...]
Frontier = tuple[tuple[int, int], ...]
RESULTS = Path(__file__).with_name("evolving_checkpoint_refinement_results.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def histories(cells: int, values: int, horizon: int) -> tuple[History, ...]:
    alphabet = tuple(itertools.product(range(cells), range(values)))
    return tuple(itertools.product(alphabet, repeat=horizon))


def empty_frontier(cells: int) -> Frontier:
    return tuple((0, -1) for _ in range(cells))


def update_frontier(frontier: Frontier, event: Event) -> Frontier:
    cell, value = event
    updated = list(frontier)
    count, _ = updated[cell]
    updated[cell] = (count + 1, value)
    return tuple(updated)


def replay_frontier(history: Sequence[Event], cells: int) -> Frontier:
    state = empty_frontier(cells)
    for event in history:
        state = update_frontier(state, event)
    return state


def combine_segments(left: Frontier, right: Frontier) -> Frontier:
    combined: list[tuple[int, int]] = []
    for (left_count, left_latest), (right_count, right_latest) in zip(left, right):
        combined.append(
            (
                left_count + right_count,
                right_latest if right_count else left_latest,
            )
        )
    return tuple(combined)


def direct_checkpoint_signature(
    history: History, boundaries: Sequence[int], cells: int
) -> tuple[Frontier, ...]:
    return tuple(replay_frontier(history[:boundary], cells) for boundary in boundaries)


def causal_segment_machine(
    history: History, boundaries: Sequence[int], cells: int
) -> tuple[Frontier, ...]:
    """Freeze the live segment exactly when each exogenous boundary arrives."""

    require(tuple(boundaries) == tuple(sorted(set(boundaries))), "unordered boundaries")
    require(
        all(1 <= boundary <= len(history) for boundary in boundaries),
        "checkpoint boundary outside positive history prefix",
    )
    boundary_set = set(boundaries)
    current = empty_frontier(cells)
    frozen: list[Frontier] = []
    for index, event in enumerate(history, start=1):
        current = update_frontier(current, event)
        if index in boundary_set:
            frozen.append(current)
            current = empty_frontier(cells)
    return tuple(frozen)


def cumulative_from_segments(segments: Sequence[Frontier], cells: int) -> tuple[Frontier, ...]:
    current = empty_frontier(cells)
    result: list[Frontier] = []
    for segment in segments:
        current = combine_segments(current, segment)
        result.append(current)
    return tuple(result)


def segment_count(length: int, cells: int, values: int) -> int:
    if length == 0:
        return 1
    return sum(
        math.comb(cells, touched)
        * math.comb(length - 1, touched - 1)
        * values**touched
        for touched in range(1, min(cells, length) + 1)
    )


def checkpoint_count(boundaries: Sequence[int], cells: int, values: int) -> int:
    require(cells > 0 and values > 0, "nonpositive event alphabet")
    require(
        tuple(boundaries) == tuple(sorted(set(boundaries)))
        and all(boundary > 0 for boundary in boundaries),
        "checkpoint boundaries must be distinct, positive, and ordered",
    )
    previous = 0
    count = 1
    for boundary in boundaries:
        count *= segment_count(boundary - previous, cells, values)
        previous = boundary
    return count


def schedules(horizon: int) -> tuple[tuple[int, ...], ...]:
    if horizon == 0:
        return ((),)
    return tuple(
        tuple(
            boundary
            for boundary in range(1, horizon)
            if mask & (1 << (boundary - 1))
        )
        + (horizon,)
        for mask in range(1 << max(0, horizon - 1))
    )


def verify_causal_refinement(
    max_cells: int = 3,
    max_values: int = 3,
    max_horizon: int = 4,
) -> dict[str, int]:
    history_schedule_pairs = 0
    for cells in range(1, max_cells + 1):
        for values in range(1, max_values + 1):
            for horizon in range(max_horizon + 1):
                words = histories(cells, values, horizon)
                for boundaries in schedules(horizon):
                    observed_segments = set()
                    observed_direct = set()
                    for history in words:
                        segments = causal_segment_machine(history, boundaries, cells)
                        cumulative = cumulative_from_segments(segments, cells)
                        direct = direct_checkpoint_signature(history, boundaries, cells)
                        require(cumulative == direct, "causal/direct signature mismatch")
                        observed_segments.add(segments)
                        observed_direct.add(direct)
                        history_schedule_pairs += 1
                    expected = checkpoint_count(boundaries, cells, values)
                    require(len(observed_segments) == expected, "segment product mismatch")
                    require(len(observed_direct) == expected, "direct product mismatch")
    return {
        "maximum_cells": max_cells,
        "maximum_values": max_values,
        "maximum_horizon": max_horizon,
        "history_schedule_pairs": history_schedule_pairs,
    }


def split_profile(
    cells: int, values: int, horizon: int, new_boundaries: Sequence[int]
) -> dict[str, object]:
    words = histories(cells, values, horizon)
    old: dict[Frontier, set[tuple[Frontier, ...]]] = defaultdict(set)
    boundaries = tuple(new_boundaries) + (horizon,)
    for history in words:
        old[replay_frontier(history, cells)].add(
            direct_checkpoint_signature(history, boundaries, cells)
        )
    profile = Counter(len(children) for children in old.values())
    return {
        "cells": cells,
        "values": values,
        "horizon": horizon,
        "new_internal_boundaries": list(new_boundaries),
        "old_states": len(old),
        "refined_states": sum(len(children) for children in old.values()),
        "split_multiplicity_histogram": {
            str(multiplicity): count for multiplicity, count in sorted(profile.items())
        },
        "maximum_tag_bits": math.ceil(math.log2(max(profile))),
    }


def rolling_window_state(history: History, cells: int, width: int) -> tuple[int, Frontier, History]:
    require(0 <= width <= len(history), "window width outside history")
    base_boundary = max(0, len(history) - width)
    return (
        base_boundary,
        replay_frontier(history[:base_boundary], cells),
        history[base_boundary:],
    )


def answer_from_window(
    state: tuple[int, Frontier, History], boundary: int
) -> tuple[Frontier, int]:
    base_boundary, base, window = state
    require(base_boundary <= boundary <= base_boundary + len(window), "outside exact window")
    frontier = base
    replayed = 0
    for event in window[: boundary - base_boundary]:
        frontier = update_frontier(frontier, event)
        replayed += 1
    return frontier, replayed


def verify_rolling_windows(
    max_cells: int = 2,
    max_values: int = 2,
    max_horizon: int = 5,
) -> dict[str, int]:
    answers_checked = 0
    maximum_replay = 0
    for cells in range(1, max_cells + 1):
        for values in range(1, max_values + 1):
            for horizon in range(max_horizon + 1):
                for width in range(horizon + 1):
                    observed_states = set()
                    for history in histories(cells, values, horizon):
                        state = rolling_window_state(history, cells, width)
                        observed_states.add(state)
                        for boundary in range(horizon - width, horizon + 1):
                            actual, replayed = answer_from_window(state, boundary)
                            expected = replay_frontier(history[:boundary], cells)
                            require(actual == expected, "rolling-window answer mismatch")
                            require(replayed <= width, "rolling-window replay bound")
                            maximum_replay = max(maximum_replay, replayed)
                            answers_checked += 1
                    expected_states = segment_count(horizon - width, cells, values) * (
                        cells * values
                    ) ** width
                    require(len(observed_states) == expected_states, "rolling-window count")

    # The same retained base frontier and suffix hide the first AB/BA boundary.
    ab = ((0, 0), (1, 0), (0, 1), (0, 1))
    ba = ((1, 0), (0, 0), (0, 1), (0, 1))
    state_ab = rolling_window_state(ab, 2, 2)
    state_ba = rolling_window_state(ba, 2, 2)
    require(state_ab == state_ba, "outside-window witness states should merge")
    require(
        replay_frontier(ab[:1], 2) != replay_frontier(ba[:1], 2),
        "outside-window witness must separate",
    )
    return {
        "answers_checked": answers_checked,
        "maximum_replay_observed": maximum_replay,
        "outside_window_counterexample_horizon": 4,
        "outside_window_width": 2,
        "separating_boundary": 1,
    }


def build_report() -> dict[str, object]:
    causal = verify_causal_refinement()
    rolling = verify_rolling_windows()
    small = split_profile(2, 2, 3, (1,))
    actual = split_profile(4, 3, 3, (1,))
    require(
        small["split_multiplicity_histogram"] == {"2": 4, "3": 8},
        "small split profile",
    )
    require(
        actual["split_multiplicity_histogram"] == {"3": 120, "4": 108},
        "actual split profile",
    )
    report = {
        "schema_version": 1,
        "evidence_label": "THEOREM plus EXACT finite crosscheck",
        "scope": {
            "event_system": (
                "fixed cell/value alphabets and immutable append-only publications; "
                "targeted invalidation is excluded"
            ),
            "checkpoint_schedule": (
                "fixed exogenous/free schedule; each signal arrives exactly at its boundary"
            ),
            "trust": "frontier summaries and retained events are authenticated",
        },
        "causal_checkpoint_theorem": {
            "states": "product_j G(gap_j)",
            "active_bits_fixed_m_v": "O(r log(1+n/r)); o(n) whenever r=o(n)",
            "archive_probes_at_declaration": 0,
            "refinement_work_per_declaration": "O(cells)",
            "answer_error": 0,
            "justification_error": 0,
        },
        "bounded_retroactivity_theorem": {
            "state": "frontier at n-w plus exact last-w events",
            "active_bits_fixed_m_v": "O(log n + w)",
            "query_replay": "at most w retained events; no refined state is persisted",
            "outside_window": "not determined in general; AB/BA witness checked",
        },
        "causal_crosscheck": causal,
        "rolling_window_crosscheck": rolling,
        "refinement_split_profiles": [small, actual],
        "maximality_boundary": (
            "relative to the segment summary, universally zero-replay additions are exactly "
            "view-determined obligations; arbitrary retroactive boundaries are not"
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
    print("Evolving checkpoint refinement")
    print(
        "  [ok] causal/direct history-schedule checks: "
        f"{report['causal_crosscheck']['history_schedule_pairs']:,}"
    )
    print(
        "  [ok] rolling-window answers: "
        f"{report['rolling_window_crosscheck']['answers_checked']:,}"
    )
    for row in report["refinement_split_profiles"]:
        print(
            f"  [ok] m={row['cells']} v={row['values']} n={row['horizon']}: "
            f"{row['old_states']} -> {row['refined_states']} "
            f"splits={row['split_multiplicity_histogram']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
