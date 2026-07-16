#!/usr/bin/env python3
"""Exact finite-horizon check for a versioned persistent-memory contract.

This is a deliberately small Phase-7 model, not evidence for literal infinite
context.  It makes a sharp contract distinction that an implementation must
not blur:

* ``current`` queries ask for the supported/refuted/conflicted/unknown status
  of each proposition now.  Their accepted justification is a signed coverage
  frontier containing the latest source version and value for *every* source.
* ``temporal`` queries ask the same question as of every prior event boundary.
  Their accepted justification is the corresponding signed coverage frontier
  at that boundary.

Events are immutable source publications.  A first positive/negative value is
an addition, a later positive/negative value is a revision, and a tombstone is
a retraction.  Values from independent sources can contradict.  Every event
increments that source/proposition version, including repeated values and
tombstones.  The enumeration horizon is therefore also the maximum reachable
per-source version.

The validator exhaustively enumerates histories and checks:

1. current answers;
2. minimum static common-certificate states (singleton accepted certificates
   make the exact minimum the number of distinct output/certificate vectors);
3. representative-independent right transitions for those certificate
   states under every event;
4. source-local immutable-ledger and exact global-history counts;
5. the temporal contract, for which the complete sequence of coverage
   frontiers reconstructs the exact event history in this model;
6. additions, revisions, retractions, contradictions, negative-evidence
   coverage, and adversarial delayed relevance;
7. every complete-frontier checkpoint schedule through the requested horizon,
   against the exact product-of-segment-summaries formula.

The current contract intentionally assumes authenticated latest-version
frontier records.  Without that external trust primitive, a latest record does
not prove that no later version was suppressed.  The temporal contract assumes
authenticated historical frontiers.  These assumptions are printed and are
part of the result.

Exit code 0 iff all exact checks and pinned small-horizon counts pass.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Sequence


ABSENT = "ABSENT"
RETRACT = "RETRACT"
SUPPORT = "+"
REFUTE = "-"
VALUES = (SUPPORT, REFUTE, RETRACT)

if not __debug__:
    raise RuntimeError("exact theorem checks require Python assertions; do not use -O")


@dataclass(frozen=True, order=True)
class Event:
    """One immutable source-version publication."""

    source: str
    proposition: str
    value: str

    def as_tuple(self) -> tuple[str, str, str]:
        return (self.source, self.proposition, self.value)


@dataclass(frozen=True, order=True)
class Query:
    """A status query; ``as_of=None`` means the current event boundary."""

    proposition: str
    as_of: int | None = None


FrontierEntry = tuple[str, int, str]
Certificate = tuple[str, str, int, tuple[FrontierEntry, ...]]
History = tuple[Event, ...]


@dataclass(frozen=True)
class HorizonCounts:
    horizon: int
    histories: int
    current_answer_states: int
    current_certificate_static_states: int
    current_certificate_right_states: int
    current_semantic_frontier_states: int
    source_local_ledger_states: int
    temporal_answer_states: int
    temporal_certificate_static_states: int
    temporal_certificate_right_states: int

    def as_dict(self) -> dict[str, int]:
        return {
            "horizon": self.horizon,
            "histories": self.histories,
            "current_answer_states": self.current_answer_states,
            "current_certificate_static_states": self.current_certificate_static_states,
            "current_certificate_right_states": self.current_certificate_right_states,
            "current_semantic_frontier_states": self.current_semantic_frontier_states,
            "source_local_ledger_states": self.source_local_ledger_states,
            "temporal_answer_states": self.temporal_answer_states,
            "temporal_certificate_static_states": self.temporal_certificate_static_states,
            "temporal_certificate_right_states": self.temporal_certificate_right_states,
        }


def event_alphabet(sources: Sequence[str], propositions: Sequence[str]) -> tuple[Event, ...]:
    return tuple(
        Event(source, proposition, value)
        for source in sources
        for proposition in propositions
        for value in VALUES
    )


def enumerate_histories(alphabet: Sequence[Event], horizon: int) -> tuple[History, ...]:
    return tuple(itertools.product(alphabet, repeat=horizon))


def cell_events(history: History, source: str, proposition: str) -> tuple[Event, ...]:
    return tuple(
        event
        for event in history
        if event.source == source and event.proposition == proposition
    )


def frontier_entry(
    history: History,
    source: str,
    proposition: str,
) -> FrontierEntry:
    events = cell_events(history, source, proposition)
    if not events:
        return (source, 0, ABSENT)
    return (source, len(events), events[-1].value)


def coverage_frontier(
    history: History,
    proposition: str,
    sources: Sequence[str],
) -> tuple[FrontierEntry, ...]:
    return tuple(frontier_entry(history, source, proposition) for source in sources)


def answer_from_entries(entries: Sequence[FrontierEntry]) -> str:
    active = {value for _, _, value in entries if value not in (ABSENT, RETRACT)}
    if active == {SUPPORT, REFUTE}:
        return "CONFLICT"
    if active == {SUPPORT}:
        return "SUPPORTED"
    if active == {REFUTE}:
        return "REFUTED"
    if not active:
        return "UNKNOWN"
    raise AssertionError(f"unexpected active value set: {active}")


def query_prefix(history: History, query: Query) -> History:
    if query.as_of is None:
        return history
    if not 0 <= query.as_of <= len(history):
        raise ValueError(f"as-of boundary {query.as_of} outside history length {len(history)}")
    return history[: query.as_of]


def answer(history: History, query: Query, sources: Sequence[str]) -> str:
    prefix = query_prefix(history, query)
    return answer_from_entries(coverage_frontier(prefix, query.proposition, sources))


def certificate(history: History, query: Query, sources: Sequence[str]) -> Certificate:
    """The unique accepted complete-coverage certificate in this contract."""

    prefix = query_prefix(history, query)
    boundary = len(history) if query.as_of is None else query.as_of
    mode = "CURRENT" if query.as_of is None else "AS_OF"
    return (
        mode,
        query.proposition,
        boundary,
        coverage_frontier(prefix, query.proposition, sources),
    )


def accepted_certificates(
    history: History,
    query: Query,
    sources: Sequence[str],
) -> frozenset[Certificate]:
    """Accepted-justification relation; singleton by explicit contract choice."""

    return frozenset((certificate(history, query, sources),))


def validate_certificate(
    history: History,
    query: Query,
    claimed_answer: str,
    cert: Certificate,
    sources: Sequence[str],
) -> bool:
    mode, proposition, boundary, entries = cert
    expected_mode = "CURRENT" if query.as_of is None else "AS_OF"
    expected_boundary = len(history) if query.as_of is None else query.as_of
    if (mode, proposition, boundary) != (
        expected_mode,
        query.proposition,
        expected_boundary,
    ):
        return False
    if tuple(source for source, _, _ in entries) != tuple(sources):
        return False
    prefix = query_prefix(history, query)
    if entries != coverage_frontier(prefix, proposition, sources):
        return False
    return claimed_answer == answer_from_entries(entries)


def current_queries(propositions: Sequence[str]) -> tuple[Query, ...]:
    return tuple(Query(proposition) for proposition in propositions)


def temporal_queries(propositions: Sequence[str], horizon: int) -> tuple[Query, ...]:
    return tuple(
        Query(proposition, boundary)
        for boundary in range(horizon + 1)
        for proposition in propositions
    )


def answer_signature(
    history: History,
    queries: Sequence[Query],
    sources: Sequence[str],
) -> tuple[str, ...]:
    return tuple(answer(history, query, sources) for query in queries)


def certificate_signature(
    history: History,
    queries: Sequence[Query],
    sources: Sequence[str],
) -> tuple[tuple[str, frozenset[Certificate]], ...]:
    return tuple(
        (
            answer(history, query, sources),
            accepted_certificates(history, query, sources),
        )
        for query in queries
    )


def current_frontier_key(
    history: History,
    sources: Sequence[str],
    propositions: Sequence[str],
) -> tuple[FrontierEntry, ...]:
    return tuple(
        frontier_entry(history, source, proposition)
        for proposition in propositions
        for source in sources
    )


def source_local_ledger_key(
    history: History,
    sources: Sequence[str],
    propositions: Sequence[str],
) -> tuple[tuple[str, ...], ...]:
    """Full per-cell value chains, with cross-cell interleaving discarded."""

    return tuple(
        tuple(event.value for event in cell_events(history, source, proposition))
        for proposition in propositions
        for source in sources
    )


def current_frontier_count_formula(horizon: int, cell_count: int) -> int:
    """Count version/latest-value frontiers after exactly ``horizon`` events.

    Choose ``r`` cells that have been updated, distribute the positive event
    counts among them, and choose one of the three latest values for each.
    """

    return frontier_segment_count(horizon, cell_count, len(VALUES))


def frontier_segment_count(length: int, cell_count: int, value_count: int) -> int:
    """Count exact count/latest-value summaries of one fixed-length segment."""

    if length < 0 or cell_count < 1 or value_count < 1:
        raise ValueError("invalid segment-count parameters")
    if length == 0:
        return 1
    return sum(
        math.comb(cell_count, populated_cells)
        * math.comb(length - 1, populated_cells - 1)
        * value_count**populated_cells
        for populated_cells in range(1, min(cell_count, length) + 1)
    )


def uniform_current_count_through(max_horizon: int, cell_count: int) -> int:
    """States for one no-free-clock machine over every depth ``<= n``.

    ``current_frontier_count_formula(n, m)`` is an exact-layer width.  Current
    certificates also contain their event boundary, so equality classes from
    different depths cannot merge when the horizon is not supplied as a free
    external clock.
    """

    return sum(
        current_frontier_count_formula(horizon, cell_count)
        for horizon in range(max_horizon + 1)
    )


def uniform_first_checkpoint_count_through(
    max_horizon: int, cell_count: int
) -> int:
    """Uniform count for checkpoint 1 plus the current endpoint at every depth."""

    if max_horizon < 0:
        raise ValueError("max_horizon must be nonnegative")
    if max_horizon == 0:
        return 1
    return 1 + current_frontier_count_formula(1, cell_count) + sum(
        checkpoint_count_formula((1, horizon), cell_count)
        for horizon in range(2, max_horizon + 1)
    )


def checkpoint_schedules(horizon: int) -> tuple[tuple[int, ...], ...]:
    """Every subset of positive boundaries containing the current horizon."""

    if horizon < 0:
        raise ValueError("horizon must be nonnegative")
    if horizon == 0:
        return ((),)
    internal = tuple(range(1, horizon))
    return tuple(
        tuple(
            boundary
            for index, boundary in enumerate(internal)
            if mask & (1 << index)
        )
        + (horizon,)
        for mask in range(1 << len(internal))
    )


def checkpoint_count_formula(
    boundaries: Sequence[int],
    cell_count: int,
    value_count: int = len(VALUES),
) -> int:
    """Exact complete-frontier signature count for exogenous checkpoints."""

    if tuple(boundaries) != tuple(sorted(set(boundaries))):
        raise ValueError("checkpoint boundaries must be strictly increasing")
    if boundaries and boundaries[0] <= 0:
        raise ValueError("positive boundaries are required; frontier zero is fixed")
    previous = 0
    factors: list[int] = []
    for boundary in boundaries:
        factors.append(frontier_segment_count(boundary - previous, cell_count, value_count))
        previous = boundary
    return math.prod(factors)


def checkpoint_frontier_key(
    history: History,
    boundaries: Sequence[int],
    sources: Sequence[str],
    propositions: Sequence[str],
) -> tuple[tuple[FrontierEntry, ...], ...]:
    if boundaries and boundaries[-1] > len(history):
        raise ValueError("checkpoint lies beyond the history")
    return tuple(
        current_frontier_key(history[:boundary], sources, propositions)
        for boundary in boundaries
    )


def source_local_ledger_count_formula(horizon: int, cell_count: int) -> int:
    """Count per-cell value chains after discarding cross-cell interleaving."""

    return math.comb(horizon + cell_count - 1, cell_count - 1) * len(VALUES) ** horizon


def partition_by_signature(
    histories: Iterable[History],
    signature,
) -> dict[object, tuple[History, ...]]:
    blocks: dict[object, list[History]] = defaultdict(list)
    for history in histories:
        blocks[signature(history)].append(history)
    return {key: tuple(members) for key, members in blocks.items()}


def check_common_certificate_blocks(
    blocks: dict[object, tuple[History, ...]],
    queries: Sequence[Query],
    sources: Sequence[str],
) -> None:
    for members in blocks.values():
        for query in queries:
            answers = {answer(history, query, sources) for history in members}
            assert len(answers) == 1
            common: set[Certificate] | None = None
            for history in members:
                accepted = set(accepted_certificates(history, query, sources))
                common = accepted if common is None else common & accepted
            assert common
            for cert in common:
                assert all(
                    validate_certificate(history, query, next(iter(answers)), cert, sources)
                    for history in members
                )


def check_layered_right_congruence(
    layers: Sequence[tuple[History, ...]],
    alph: Sequence[Event],
    signatures: Sequence[dict[History, object]],
) -> tuple[bool, dict[str, object] | None]:
    """Check right transitions for every same-signature pair at each nonterminal layer."""

    for depth in range(len(layers) - 1):
        blocks: dict[object, list[History]] = defaultdict(list)
        for history in layers[depth]:
            blocks[signatures[depth][history]].append(history)
        for block_signature, members in blocks.items():
            if len(members) < 2:
                continue
            representative = members[0]
            for event in alph:
                destination = signatures[depth + 1][representative + (event,)]
                for other in members[1:]:
                    other_destination = signatures[depth + 1][other + (event,)]
                    if other_destination != destination:
                        return False, {
                            "depth": depth,
                            "source_signature": repr(block_signature),
                            "history_a": history_to_json(representative),
                            "history_b": history_to_json(other),
                            "event": event.as_tuple(),
                            "destination_a": repr(destination),
                            "destination_b": repr(other_destination),
                        }
    return True, None


def event_kind(history_before: History, event: Event) -> str:
    prior = cell_events(history_before, event.source, event.proposition)
    if event.value == RETRACT:
        return "RETRACTION"
    return "ADDITION" if not prior else "REVISION"


def history_to_json(history: History) -> list[list[str]]:
    return [list(event.as_tuple()) for event in history]


def assert_contract_semantics(sources: Sequence[str], propositions: Sequence[str]) -> dict[str, object]:
    alice, bob = sources
    alpha, beta = propositions

    add = Event(alice, alpha, SUPPORT)
    revise = Event(alice, alpha, REFUTE)
    retract = Event(alice, alpha, RETRACT)
    contradict = Event(bob, alpha, REFUTE)

    assert event_kind((), add) == "ADDITION"
    assert event_kind((add,), revise) == "REVISION"
    assert event_kind((add,), retract) == "RETRACTION"

    revised = (add, revise)
    assert answer(revised, Query(alpha), sources) == "REFUTED"
    assert frontier_entry(revised, alice, alpha) == (alice, 2, REFUTE)
    assert answer(revised, Query(alpha, 1), sources) == "SUPPORTED"

    retracted = (add, retract)
    assert answer(retracted, Query(alpha), sources) == "UNKNOWN"
    negative = certificate(retracted, Query(alpha), sources)
    assert negative[3] == ((alice, 2, RETRACT), (bob, 0, ABSENT))
    assert validate_certificate(retracted, Query(alpha), "UNKNOWN", negative, sources)

    conflict = (add, Event(alice, beta, SUPPORT), contradict)
    assert answer(conflict, Query(alpha), sources) == "CONFLICT"
    conflict_cert = certificate(conflict, Query(alpha), sources)
    assert {entry[2] for entry in conflict_cert[3]} == {SUPPORT, REFUTE}

    # Delayed relevance: proposition-factorized alpha semantics merge these
    # histories under any shared continuation.  The loop exactly checks short
    # continuations as a regression test; the general statement follows because
    # filtering either extended history to alpha produces the same sequence.
    # Adding a beta query later separates them.  A fixed contract that anticipated
    # beta would never merge them.
    delayed_a = (Event(alice, beta, SUPPORT),)
    delayed_b = (Event(alice, beta, REFUTE),)
    alpha_queries = (Query(alpha),)
    assert certificate_signature(delayed_a, alpha_queries, sources) == certificate_signature(
        delayed_b, alpha_queries, sources
    )
    alph = event_alphabet(sources, propositions)
    assert tuple(
        event for event in delayed_a if event.proposition == alpha
    ) == tuple(event for event in delayed_b if event.proposition == alpha)
    for continuation_length in range(3):
        for continuation in itertools.product(alph, repeat=continuation_length):
            assert certificate_signature(
                delayed_a + continuation, alpha_queries, sources
            ) == certificate_signature(delayed_b + continuation, alpha_queries, sources)
    delayed_query = Query(beta, 1)
    assert answer(delayed_a, delayed_query, sources) == "SUPPORTED"
    assert answer(delayed_b, delayed_query, sources) == "REFUTED"

    # Answer-only current state is not continuation sufficient: hidden source
    # attribution changes the result of a later retraction.
    answer_a = (Event(alice, alpha, SUPPORT),)
    answer_b = (Event(bob, alpha, SUPPORT),)
    assert answer_signature(answer_a, current_queries(propositions), sources) == answer_signature(
        answer_b, current_queries(propositions), sources
    )
    continuation = Event(alice, alpha, RETRACT)
    assert answer(answer_a + (continuation,), Query(alpha), sources) == "UNKNOWN"
    assert answer(answer_b + (continuation,), Query(alpha), sources) == "SUPPORTED"

    # Retrospective-query failure: AB and BA have the same complete current
    # frontier, but their frontier at boundary one differs.  A checkpoint not
    # declared before compression cannot be recovered from current state alone.
    event_a = Event(alice, alpha, SUPPORT)
    event_b = Event(bob, alpha, SUPPORT)
    ordered_ab = (event_a, event_b)
    ordered_ba = (event_b, event_a)
    assert current_frontier_key(ordered_ab, sources, propositions) == current_frontier_key(
        ordered_ba, sources, propositions
    )
    boundary_one = (1,)
    assert checkpoint_frontier_key(
        ordered_ab, boundary_one, sources, propositions
    ) != checkpoint_frontier_key(ordered_ba, boundary_one, sources, propositions)

    return {
        "revision_trace": history_to_json(revised),
        "retraction_trace": history_to_json(retracted),
        "contradiction_trace": history_to_json(conflict),
        "delayed_relevance_pair": [history_to_json(delayed_a), history_to_json(delayed_b)],
        "answer_only_right_failure": {
            "histories": [history_to_json(answer_a), history_to_json(answer_b)],
            "continuation": list(continuation.as_tuple()),
            "destinations": ["UNKNOWN", "SUPPORTED"],
        },
        "retroactive_checkpoint_failure": {
            "histories": [history_to_json(ordered_ab), history_to_json(ordered_ba)],
            "shared_current_frontier": True,
            "separating_boundary": 1,
        },
    }


def build_report(max_horizon: int = 3) -> dict[str, object]:
    if max_horizon < 1:
        raise ValueError("max_horizon must be at least 1")
    # Pinned names make the semantic assertions and JSON stable.
    sources = ("alice", "bob")
    propositions = ("alpha", "beta")
    alph = event_alphabet(sources, propositions)
    layers = tuple(enumerate_histories(alph, horizon) for horizon in range(max_horizon + 1))

    current_signatures: list[dict[History, object]] = []
    temporal_signatures: list[dict[History, object]] = []
    counts: list[HorizonCounts] = []
    checkpoint_sweep: list[dict[str, object]] = []

    for horizon, histories in enumerate(layers):
        cq = current_queries(propositions)
        tq = temporal_queries(propositions, horizon)
        current_answer = partition_by_signature(
            histories, lambda history: answer_signature(history, cq, sources)
        )
        current_cert = partition_by_signature(
            histories, lambda history: certificate_signature(history, cq, sources)
        )
        temporal_answer = partition_by_signature(
            histories, lambda history: answer_signature(history, tq, sources)
        )
        temporal_cert = partition_by_signature(
            histories, lambda history: certificate_signature(history, tq, sources)
        )
        local_ledgers = {
            source_local_ledger_key(history, sources, propositions) for history in histories
        }
        frontiers = {current_frontier_key(history, sources, propositions) for history in histories}

        # With singleton accepted certificates, distinct certificate signatures
        # cannot share a valid block, and each equality block is valid.  Thus the
        # equality partition is the exact minimum static common-certificate
        # partition, not merely a selected construction.
        check_common_certificate_blocks(current_cert, cq, sources)
        check_common_certificate_blocks(temporal_cert, tq, sources)
        assert len(frontiers) == len(current_cert)
        cell_count = len(sources) * len(propositions)
        assert len(frontiers) == current_frontier_count_formula(horizon, cell_count)
        assert len(local_ledgers) == source_local_ledger_count_formula(horizon, cell_count)
        assert len(histories) == len(alph) ** horizon
        assert len(temporal_cert) == len(histories), (
            "complete historical frontier certificates should reconstruct every event",
            horizon,
        )

        schedule_rows: list[dict[str, object]] = []
        for boundaries in checkpoint_schedules(horizon):
            observed = len(
                {
                    checkpoint_frontier_key(
                        history, boundaries, sources, propositions
                    )
                    for history in histories
                }
            )
            expected = checkpoint_count_formula(boundaries, cell_count)
            assert observed == expected
            schedule_rows.append(
                {
                    "boundaries": list(boundaries),
                    "states": observed,
                    "gap_factors": [
                        frontier_segment_count(
                            boundary - (boundaries[index - 1] if index else 0),
                            cell_count,
                            len(VALUES),
                        )
                        for index, boundary in enumerate(boundaries)
                    ],
                }
            )
        checkpoint_sweep.append(
            {"horizon": horizon, "schedules": schedule_rows}
        )

        current_map = {
            history: certificate_signature(history, cq, sources) for history in histories
        }
        temporal_map = {
            history: certificate_signature(history, tq, sources) for history in histories
        }
        current_signatures.append(current_map)
        temporal_signatures.append(temporal_map)

        counts.append(
            HorizonCounts(
                horizon=horizon,
                histories=len(histories),
                current_answer_states=len(current_answer),
                current_certificate_static_states=len(current_cert),
                # Filled with the same count after the explicit right check below.
                current_certificate_right_states=len(current_cert),
                current_semantic_frontier_states=len(frontiers),
                source_local_ledger_states=len(local_ledgers),
                temporal_answer_states=len(temporal_answer),
                temporal_certificate_static_states=len(temporal_cert),
                temporal_certificate_right_states=len(temporal_cert),
            )
        )

    current_right, current_failure = check_layered_right_congruence(
        layers, alph, current_signatures
    )
    temporal_right, temporal_failure = check_layered_right_congruence(
        layers, alph, temporal_signatures
    )
    assert current_right, current_failure
    assert temporal_right, temporal_failure

    semantics = assert_contract_semantics(sources, propositions)

    # Exact regression anchors.  The formulas are independent checks on the
    # enumeration rather than values inferred from its output.
    pinned_through_three = {
        0: (1, 1, 1, 1),
        1: (12, 5, 12, 12),
        2: (144, 11, 66, 90),
        3: (1728, 15, 228, 540),
    }
    for row in counts:
        if row.horizon not in pinned_through_three:
            continue
        expected_history, expected_answers, expected_frontiers, expected_ledgers = (
            pinned_through_three[row.horizon]
        )
        assert row.histories == expected_history
        assert row.current_answer_states == expected_answers
        assert row.current_certificate_static_states == expected_frontiers
        assert row.current_certificate_right_states == expected_frontiers
        assert row.current_semantic_frontier_states == expected_frontiers
        assert row.source_local_ledger_states == expected_ledgers
        assert row.temporal_certificate_static_states == expected_history
        assert row.temporal_certificate_right_states == expected_history

    checkpoint_anchors = {
        (4,): 579,
        (1, 4): 2_736,
        (2, 4): 4_356,
        (1, 2, 4): 9_504,
        (1, 2, 3, 4): 20_736,
    }
    for boundaries, expected in checkpoint_anchors.items():
        assert checkpoint_count_formula(boundaries, 4) == expected
    assert uniform_current_count_through(4, 4) == 886
    assert uniform_first_checkpoint_count_through(4, 4) == 3_685
    if max_horizon >= 4:
        horizon_four = checkpoint_sweep[4]
        observed = {
            tuple(schedule["boundaries"]): schedule["states"]
            for schedule in horizon_four["schedules"]
        }
        assert all(
            observed[boundaries] == expected
            for boundaries, expected in checkpoint_anchors.items()
        )

    return {
        "schema_version": 2,
        "evidence_label": "EXACT finite enumeration",
        "contract": {
            "sources": list(sources),
            "propositions": list(propositions),
            "event_values": list(VALUES),
            "event_alphabet_size": len(alph),
            "maximum_history_horizon": max_horizon,
            "maximum_reachable_per_cell_source_version": max_horizon,
            "answers": ["UNKNOWN", "SUPPORTED", "REFUTED", "CONFLICT"],
            "accepted_justification": (
                "one authenticated complete source-coverage frontier per query"
            ),
        },
        "counts": [row.as_dict() for row in counts],
        "count_semantics": {
            "rows": "exact-length layers with the horizon supplied externally",
            "uniform_machine_without_free_clock": {
                "through_horizon": max_horizon,
                "current_certificate_states": uniform_current_count_through(
                    max_horizon, len(sources) * len(propositions)
                ),
                "checkpoint_one_plus_current_states": (
                    uniform_first_checkpoint_count_through(
                        max_horizon, len(sources) * len(propositions)
                    )
                ),
                "reason_layers_do_not_merge": (
                    "the unique accepted certificate contains its event boundary"
                ),
            },
        },
        "checkpoint_sweep": checkpoint_sweep,
        "right_congruence": {
            "current": current_right,
            "current_failure": current_failure,
            "temporal": temporal_right,
            "temporal_failure": temporal_failure,
        },
        "semantic_checks": semantics,
        "assumptions": [
            "The source set, proposition set, answer semantics, and query contract are fixed.",
            "Events have one authenticated global order, and every as-of boundary is an event prefix.",
            "Latest-version and historical frontiers are authenticated and cannot omit a source.",
            "The exact immutable archive grows with the event history.",
            "The active current certificate stores source version and latest value, not each prior value.",
            "The enumeration is finite-horizon; it does not prove bounded state for unbounded versions.",
            "A later query outside the declared contract requires exact fallback or contract refinement.",
            "Checkpoint boundaries are exogenous; retroactively requested old boundaries require fallback.",
        ],
        "verification_cost_scope": {
            "checker": "reference checker recomputes the claimed frontier from raw history",
            "event_predicate_checks_per_current_query_at_boundary_n": (
                f"{len(sources)} * n"
            ),
            "local_authenticated_completeness_proof_implemented": False,
            "consequence": (
                "the quotient theorem is conditional on authenticated complete frontiers; "
                "this script does not establish archive-dormant negative-evidence checking"
            ),
        },
        "interpretation": {
            "established": (
                "For this finite contract, current complete-coverage certificate states form a "
                "right congruence and discard cross-cell interleaving; complete all-as-of "
                "certificates reconstruct the exact history."
            ),
            "elementary_counting_law": (
                "For fixed m source-proposition cells and v=3 event values, current frontier "
                "states in the exact length-n layer equal sum_r C(m,r) C(n-1,r-1) "
                "v^r (n>0), hence are Theta(n^(m-1)); exact histories equal (m v)^n. "
                "Without a free clock, the uniform machine through n uses the sum of "
                "these layer counts, Theta(n^m). Both require only Theta(log n) bits "
                "for fixed m."
            ),
            "checkpoint_factorization_theorem": (
                "For fixed 0=t_0<...<t_k=n, complete-frontier certificate states "
                "equal product_j G(t_j-t_(j-1)), where G(l) counts one segment's "
                "per-cell increments and final values."
            ),
            "arbitrary_boundary_theorem": (
                "If one exact complete-frontier query may target any boundary chosen "
                "after ingestion, the query family distinguishes every event history."
            ),
            "inference": (
                "Compactness depends on the temporal and provenance contract, not only on the "
                "underlying facts."
            ),
            "not_established": (
                "No claim of literal infinite context, novelty, or practical language-model "
                "performance follows from this fixed-ontology model."
            ),
        },
    }


def print_report(report: dict[str, object]) -> None:
    contract = report["contract"]
    assert isinstance(contract, dict)
    print(
        "Versioned memory contract: "
        f"{len(contract['sources'])} sources, {len(contract['propositions'])} propositions, "
        f"{contract['event_alphabet_size']} events"
    )
    print(
        f"{'h':>2} {'hist':>7} {'answer':>7} {'cert-static':>12} "
        f"{'cert-right':>11} {'local-log':>10} {'temp-answer':>12} "
        f"{'temp-cert':>10}"
    )
    counts = report["counts"]
    assert isinstance(counts, list)
    for row in counts:
        assert isinstance(row, dict)
        print(
            f"{row['horizon']:2d} {row['histories']:7d} "
            f"{row['current_answer_states']:7d} "
            f"{row['current_certificate_static_states']:12d} "
            f"{row['current_certificate_right_states']:11d} "
            f"{row['source_local_ledger_states']:10d} "
            f"{row['temporal_answer_states']:12d} "
            f"{row['temporal_certificate_static_states']:10d}"
        )
    print("\n[ok] all current certificate blocks have a common sound certificate")
    print("[ok] current certificate quotient has representative-independent right transitions")
    print("[ok] complete temporal certificates reconstruct every checked history")
    print("[ok] additions, revisions, retractions, contradictions, and negative evidence checked")
    print("[ok] delayed-query adversary separates histories merged by the narrower contract")
    print("[ok] every complete-frontier checkpoint schedule matches the exact product law")
    print("\nBoundary: current justified state compresses interleavings; complete all-as-of")
    print("justification is identity-like on this event model.  Both claims are finite-horizon.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-horizon", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = build_report(args.max_horizon)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
