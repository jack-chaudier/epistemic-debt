#!/usr/bin/env python3
"""Deterministic reference benchmark for exact evolving memory contracts.

The benchmark is deliberately model-free.  It compares eight memory strategies
on one immutable versioned archive containing additions, revisions, retractions,
contradictions, invalidations, delayed relevance, exact wording, temporal
queries, complete negative evidence, and new key obligations under a fixed
query language.

All emitted assertions pass a structural gate relative to a caller-supplied
trusted frontier and are independently compared with exact replay.  Compact
strategies fall back rather than emit an unsupported answer.  The stable-key
strategy charges index writes, posting-list reads, logical refinement writes,
proof bytes, and fallback separately.

The index and active state are trusted exact data structures in this executable;
this is a deterministic semantic benchmark, not a cryptographic authentication
implementation or an information-theoretic storage theorem.  A production
design would need a binding authenticated
dictionary and would have to charge its proof/verification costs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


HERE = Path(__file__).resolve().parent
ITEMS = HERE / "items.jsonl"
RAW = HERE / "responses_raw.jsonl"
SCORED = HERE / "scored.csv"
RESULTS = HERE / "reference_results.json"
DESIGN = HERE / "prereg_reference.md"
SOURCES = ("atlas", "boreal", "cygnus")
INITIAL_KEYS = ("bridge", "launch")
WINDOW = 6
ABSENT = "ABSENT"
RETRACT = "RETRACT"
VALUES = ("+", "-")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


PostingIndex = dict[str, list[int]]


def indexed_positions(
    postings: PostingIndex, key: str, boundary: int | None = None
) -> tuple[list[int], int]:
    """Read one posting list, charging search and returned index entries."""

    positions = postings.get(key, ())
    if boundary is None:
        return list(positions), 1 + len(positions)
    low = 0
    high = len(positions)
    reads = 1
    while low < high:
        middle = (low + high) // 2
        reads += 1
        if positions[middle] < boundary:
            low = middle + 1
        else:
            high = middle
    reads += low
    return list(positions[:low]), reads


def has_position_at_or_after(
    postings: PostingIndex, key: str, boundary: int
) -> tuple[bool, int]:
    """Test for a suffix posting with one directory read plus search probes.

    Unlike ``indexed_positions``, this predicate does not materialize the
    returned prefix, so it does not charge reads for entries it never returns.
    """

    positions = postings.get(key, ())
    reads = 1
    low = 0
    high = len(positions)
    while low < high:
        middle = (low + high) // 2
        reads += 1
        if positions[middle] < boundary:
            low = middle + 1
        else:
            high = middle
    return low < len(positions), reads


@dataclass(frozen=True)
class Event:
    seq: int
    source: str
    key: str
    source_version: int
    operation: str
    value: str | None
    exact_text: str
    target_version: int | None = None

    def payload(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "source": self.source,
            "key": self.key,
            "source_version": self.source_version,
            "operation": self.operation,
            "value": self.value,
            "exact_text": self.exact_text,
            "target_version": self.target_version,
        }


@dataclass(frozen=True)
class Query:
    id: str
    key: str
    mode: str
    as_of: int | None = None
    source: str | None = None
    refine_on_miss: bool = False

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "key": self.key,
            "mode": self.mode,
            "as_of": self.as_of,
            "source": self.source,
            "refine_on_miss": self.refine_on_miss,
        }


@dataclass
class Ledger:
    queries: int = 0
    local_hits: int = 0
    primary_archive_queries: int = 0
    fallbacks: int = 0
    archive_event_reads: int = 0
    query_archive_reads: int = 0
    update_archive_reads: int = 0
    index_entry_reads: int = 0
    query_index_reads: int = 0
    update_index_reads: int = 0
    verifier_archive_reads: int = 0
    local_state_reads: int = 0
    verifier_entries_checked: int = 0
    index_writes: int = 0
    auxiliary_index_bytes: int = 0
    update_work: int = 0
    refinement_work: int = 0
    proof_entries_emitted: int = 0
    proof_bytes_emitted: int = 0
    answer_errors: int = 0
    justification_errors: int = 0
    unsupported_assertions: int = 0
    blocked_local_attempts: int = 0
    peak_active_units: int = 0
    final_active_units: int = 0
    peak_active_bytes: int = 0
    final_active_bytes: int = 0

    def payload(self) -> dict[str, int]:
        return dict(self.__dict__)


@dataclass
class Archive:
    events: list[Event]
    postings: dict[str, list[int]]
    root_digest: str

    @classmethod
    def build(cls, events: Sequence[Event]) -> "Archive":
        postings: dict[str, list[int]] = {}
        for index, event in enumerate(events):
            postings.setdefault(event.key, []).append(index)
        payload = canonical([event.payload() for event in events]).encode()
        return cls(list(events), postings, hashlib.sha256(payload).hexdigest())

    def indexed_positions(
        self, key: str, boundary: int | None = None
    ) -> tuple[list[int], int]:
        """Return posting positions and exact directory/binary-search reads.

        One read selects the key's posting list.  A bounded prefix then uses
        an explicit binary search, with every inspected posting charged, and
        materializing the result charges every returned posting entry.  The
        returned archive event records are charged separately by the caller.
        """

        return indexed_positions(self.postings, key, boundary)

    def positions(self, key: str, boundary: int | None = None) -> list[int]:
        return self.indexed_positions(key, boundary)[0]

    def has_position_at_or_after(self, key: str, boundary: int) -> tuple[bool, int]:
        return has_position_at_or_after(self.postings, key, boundary)

    def event_bytes(self) -> int:
        return len(canonical([event.payload() for event in self.events]).encode())

    def index_bytes(self) -> int:
        return len(canonical(self.postings).encode())

    def digest(self) -> str:
        return self.root_digest


Entry = tuple[str, int, str, str, int]
Frontier = tuple[Entry, ...]


def source_frontier(events: Sequence[Event], source: str) -> Entry:
    invalidated: set[int] = set()
    for event in events:
        if event.operation == "INVALIDATE":
            require(event.target_version is not None, "invalidation missing target")
            invalidated.add(event.target_version)
    candidates = [
        event
        for event in events
        if event.operation in ("SET", "RETRACT")
        and event.source_version not in invalidated
    ]
    if not candidates:
        return (source, 0, ABSENT, "", 0)
    latest = max(candidates, key=lambda event: event.source_version)
    value = RETRACT if latest.operation == "RETRACT" else str(latest.value)
    text = "" if latest.operation == "RETRACT" else latest.exact_text
    return (source, latest.source_version, value, text, latest.seq)


def frontier_from_events(events: Sequence[Event], key: str) -> Frontier:
    return tuple(
        source_frontier(
            tuple(event for event in events if event.key == key and event.source == source),
            source,
        )
        for source in SOURCES
    )


def status_answer(frontier: Frontier) -> str:
    active = {entry[2] for entry in frontier if entry[2] in VALUES}
    if active == {"+", "-"}:
        return "CONFLICT"
    if active == {"+"}:
        return "SUPPORTED"
    if active == {"-"}:
        return "REFUTED"
    return "UNKNOWN"


def answer_from_frontier(query: Query, frontier: Frontier) -> object:
    if query.mode == "status":
        return status_answer(frontier)
    require(query.mode == "source_exact", f"unknown query mode {query.mode}")
    require(query.source in SOURCES, "source_exact requires a declared source")
    entry = next(entry for entry in frontier if entry[0] == query.source)
    return {
        "source": entry[0],
        "source_version": entry[1],
        "value": entry[2],
        "exact_text": entry[3],
        "event_seq": entry[4],
    }


def certificate(
    query: Query,
    frontier: Frontier,
    answer: object,
    boundary: int,
    archive_digest: str,
) -> dict[str, object]:
    return {
        "key": query.key,
        "mode": query.mode,
        "boundary": boundary,
        "source": query.source,
        "complete_sources": list(SOURCES),
        "source_universe_sha256": hashlib.sha256(
            canonical(list(SOURCES)).encode()
        ).hexdigest(),
        "archive_sha256": archive_digest,
        "entries": [list(entry) for entry in frontier],
        "answer": answer,
    }


def structural_gate(
    query: Query,
    answer: object,
    proof: dict[str, object],
    trusted_frontier: Frontier,
    archive: Archive,
) -> bool:
    expected_boundary = len(archive.events) if query.as_of is None else query.as_of
    if proof.get("key") != query.key or proof.get("mode") != query.mode:
        return False
    if proof.get("boundary") != expected_boundary or proof.get("source") != query.source:
        return False
    if proof.get("complete_sources") != list(SOURCES):
        return False
    if proof.get("source_universe_sha256") != hashlib.sha256(
        canonical(list(SOURCES)).encode()
    ).hexdigest():
        return False
    if proof.get("archive_sha256") != archive.digest():
        return False
    raw_entries = proof.get("entries")
    if not isinstance(raw_entries, list) or len(raw_entries) != len(SOURCES):
        return False
    try:
        entries = tuple(
            (str(row[0]), int(row[1]), str(row[2]), str(row[3]), int(row[4]))
            for row in raw_entries
        )
    except (IndexError, TypeError, ValueError):
        return False
    if tuple(entry[0] for entry in entries) != SOURCES:
        return False
    if entries != trusted_frontier:
        return False
    return proof.get("answer") == answer == answer_from_frontier(query, entries)


def oracle(
    archive: Archive,
    query: Query,
    access: str,
    postings: PostingIndex | None = None,
) -> tuple[object, dict[str, object], Frontier, int, int]:
    boundary = len(archive.events) if query.as_of is None else query.as_of
    require(0 <= boundary <= len(archive.events), "query boundary outside archive")
    if access == "full":
        selected = archive.events[:boundary]
        event_reads = boundary
        index_reads = 0
    elif access == "index":
        require(postings is not None, "indexed oracle requires an explicit index")
        positions, index_reads = indexed_positions(postings, query.key, boundary)
        selected = [archive.events[index] for index in positions]
        event_reads = len(positions)
    else:
        raise ValueError(access)
    frontier = frontier_from_events(selected, query.key)
    answer = answer_from_frontier(query, frontier)
    return (
        answer,
        certificate(query, frontier, answer, boundary, archive.digest()),
        frontier,
        event_reads,
        index_reads,
    )


def independent_oracle(
    archive: Archive, query: Query
) -> tuple[object, dict[str, object]]:
    """Direct replay implementation independent of the primary frontier code."""

    boundary = len(archive.events) if query.as_of is None else query.as_of
    require(0 <= boundary <= len(archive.events), "query boundary outside archive")
    records: dict[str, dict[int, Event]] = {source: {} for source in SOURCES}
    invalidated: dict[str, set[int]] = {source: set() for source in SOURCES}
    for event in archive.events[:boundary]:
        if event.key != query.key:
            continue
        if event.operation == "INVALIDATE":
            require(event.target_version is not None, "invalidation target")
            invalidated[event.source].add(event.target_version)
        else:
            records[event.source][event.source_version] = event

    entries: list[Entry] = []
    for source in SOURCES:
        valid_versions = [
            version
            for version in records[source]
            if version not in invalidated[source]
        ]
        if not valid_versions:
            entries.append((source, 0, ABSENT, "", 0))
            continue
        latest = records[source][max(valid_versions)]
        if latest.operation == "RETRACT":
            entries.append((source, latest.source_version, RETRACT, "", latest.seq))
        else:
            require(latest.value in VALUES, "independent SET value")
            entries.append(
                (
                    source,
                    latest.source_version,
                    str(latest.value),
                    latest.exact_text,
                    latest.seq,
                )
            )
    frontier = tuple(entries)

    if query.mode == "status":
        active = {entry[2] for entry in frontier if entry[2] in VALUES}
        if active == {"+", "-"}:
            answer: object = "CONFLICT"
        elif active == {"+"}:
            answer = "SUPPORTED"
        elif active == {"-"}:
            answer = "REFUTED"
        else:
            answer = "UNKNOWN"
    else:
        require(query.mode == "source_exact", "independent query mode")
        require(query.source in SOURCES, "independent source")
        entry = next(item for item in frontier if item[0] == query.source)
        answer = {
            "source": entry[0],
            "source_version": entry[1],
            "value": entry[2],
            "exact_text": entry[3],
            "event_seq": entry[4],
        }

    proof = {
        "key": query.key,
        "mode": query.mode,
        "boundary": boundary,
        "source": query.source,
        "complete_sources": list(SOURCES),
        "source_universe_sha256": hashlib.sha256(
            canonical(list(SOURCES)).encode()
        ).hexdigest(),
        "archive_sha256": archive.digest(),
        "entries": [list(entry) for entry in frontier],
        "answer": answer,
    }
    return answer, proof


def load_items() -> tuple[tuple[Event, ...], tuple[int, ...], tuple[Query, ...]]:
    raw = [json.loads(line) for line in ITEMS.read_text().splitlines() if line.strip()]
    events: list[Event] = []
    checkpoints: list[int] = []
    queries: list[Query] = []
    versions: dict[tuple[str, str], int] = {}
    material_versions: dict[tuple[str, str], set[int]] = {}
    queries_started = False
    for item in raw:
        kind = item["type"]
        if kind == "event":
            require(not queries_started, "events after queries are outside this fixture")
            key = (str(item["source"]), str(item["key"]))
            versions[key] = versions.get(key, 0) + 1
            event = Event(
                seq=len(events) + 1,
                source=key[0],
                key=key[1],
                source_version=versions[key],
                operation=str(item["operation"]),
                value=item.get("value"),
                exact_text=str(item.get("exact_text", "")),
                target_version=(
                    int(item["target_version"])
                    if item.get("target_version") is not None
                    else None
                ),
            )
            require(event.source in SOURCES, "undeclared source")
            require(event.operation in ("SET", "RETRACT", "INVALIDATE"), "operation")
            if event.operation == "SET":
                require(event.value in VALUES and bool(event.exact_text), "invalid SET")
            elif event.operation == "RETRACT":
                require(event.value is None, "retraction must not carry a value")
            else:
                require(event.target_version is not None, "invalidation target")
                require(
                    event.target_version in material_versions.get(key, set()),
                    "invalidation must target an earlier material source version",
                )
            if event.operation in ("SET", "RETRACT"):
                material_versions.setdefault(key, set()).add(event.source_version)
            events.append(event)
        elif kind == "checkpoint":
            require(not queries_started, "checkpoints after queries are outside this fixture")
            boundary = int(item["boundary"])
            require(boundary > 0, "checkpoint boundary must be positive")
            require(boundary == len(events), "checkpoint must be declared causally")
            checkpoints.append(boundary)
        elif kind == "query":
            queries_started = True
            queries.append(
                Query(
                    id=str(item["id"]),
                    key=str(item["key"]),
                    mode=str(item["mode"]),
                    as_of=int(item["as_of"]) if item.get("as_of") is not None else None,
                    source=str(item["source"]) if item.get("source") is not None else None,
                    refine_on_miss=bool(item.get("refine_on_miss", False)),
                )
            )
        else:
            raise ValueError(kind)
    require(checkpoints == sorted(set(checkpoints)), "duplicate/unordered checkpoints")
    return tuple(events), tuple(checkpoints), tuple(queries)


def all_keys(events: Sequence[Event]) -> tuple[str, ...]:
    return tuple(sorted({event.key for event in events}))


def frontiers_at(
    archive: Archive, keys: Iterable[str], boundary: int
) -> dict[str, Frontier]:
    prefix = archive.events[:boundary]
    return {key: frontier_from_events(prefix, key) for key in keys}


@dataclass
class StrategyState:
    name: str
    archive: Archive
    checkpoints: tuple[int, ...]
    ledger: Ledger = field(default_factory=Ledger)
    current: dict[str, Frontier] = field(default_factory=dict)
    snapshots: dict[tuple[str, int], Frontier] = field(default_factory=dict)
    answers: dict[str, object] = field(default_factory=dict)
    witnesses: dict[str, Entry] = field(default_factory=dict)
    active_history: tuple[Event, ...] = ()
    rolling_base_boundary: int = 0
    rolling_base: dict[str, Frontier] = field(default_factory=dict)
    rolling_events: tuple[Event, ...] = ()
    posting_index: PostingIndex = field(default_factory=dict)

    def active_units(self) -> int:
        if self.name == "full_history_active":
            return len(self.active_history)
        if self.name == "full_replay":
            return 0
        if self.name == "current_answer":
            return len(self.answers)
        if self.name == "exact_witness":
            return len(self.witnesses)
        if self.name == "rolling_exact_window":
            return sum(len(value) for value in self.rolling_base.values()) + len(
                self.rolling_events
            )
        return sum(len(value) for value in self.current.values()) + sum(
            len(value) for value in self.snapshots.values()
        )

    def active_payload(self) -> object:
        """Canonical logical state payload used for commensurate byte counts."""

        if self.name == "full_history_active":
            return [event.payload() for event in self.active_history]
        if self.name == "full_replay":
            return {}
        if self.name == "current_answer":
            return self.answers
        if self.name == "exact_witness":
            return self.witnesses
        if self.name == "rolling_exact_window":
            return {
                "base_boundary": self.rolling_base_boundary,
                "base": self.rolling_base,
                "events": [event.payload() for event in self.rolling_events],
            }
        return {
            "current": self.current,
            "snapshots": [
                {"key": key, "boundary": boundary, "frontier": frontier}
                for (key, boundary), frontier in sorted(self.snapshots.items())
            ],
        }

    def active_bytes(self) -> int:
        if self.name == "full_replay":
            return 0
        return len(canonical(self.active_payload()).encode())

    @staticmethod
    def empty_frontier() -> Frontier:
        return tuple((source, 0, ABSENT, "", 0) for source in SOURCES)

    def apply_event_to_frontiers(
        self,
        frontiers: dict[str, Frontier],
        event: Event,
        *,
        indexed_repair: bool,
    ) -> None:
        """Apply one ingested event, charging any invalidation repair."""

        frontier = list(frontiers.setdefault(event.key, self.empty_frontier()))
        source_index = SOURCES.index(event.source)
        current = frontier[source_index]
        if event.operation == "SET":
            frontier[source_index] = (
                event.source,
                event.source_version,
                str(event.value),
                event.exact_text,
                event.seq,
            )
        elif event.operation == "RETRACT":
            frontier[source_index] = (
                event.source,
                event.source_version,
                RETRACT,
                "",
                event.seq,
            )
        elif current[1] == event.target_version:
            if indexed_repair:
                positions, index_reads = indexed_positions(
                    self.posting_index,
                    event.key, event.seq
                )
                selected = [self.archive.events[position] for position in positions]
                event_reads = len(positions)
                self.ledger.index_entry_reads += index_reads
                self.ledger.update_index_reads += index_reads
            else:
                selected = self.archive.events[: event.seq]
                event_reads = event.seq
            cell = tuple(
                item
                for item in selected
                if item.key == event.key and item.source == event.source
            )
            frontier[source_index] = source_frontier(cell, event.source)
            self.ledger.archive_event_reads += event_reads
            self.ledger.update_archive_reads += event_reads
        frontiers[event.key] = tuple(frontier)

    def record_active_size(self) -> None:
        units = self.active_units()
        byte_count = self.active_bytes()
        self.ledger.peak_active_units = max(self.ledger.peak_active_units, units)
        self.ledger.peak_active_bytes = max(
            self.ledger.peak_active_bytes, byte_count
        )
        self.ledger.final_active_units = units
        self.ledger.final_active_bytes = byte_count

    def initialize(self) -> None:
        final = len(self.archive.events)
        if self.name == "full_history_active":
            ingested: list[Event] = []
            for event in self.archive.events:
                ingested.append(event)
                self.active_history = tuple(ingested)
                self.ledger.update_work += 1
                self.record_active_size()
        elif self.name == "full_replay":
            self.ledger.update_work = 0
        elif self.name in ("current_answer", "exact_witness"):
            # These deliberately insufficient summaries are compiled by exact
            # replay after ingestion.  The replay is charged; they are not
            # claimed to be self-maintainable under revisions/invalidation.
            for key in INITIAL_KEYS:
                frontier = frontier_from_events(self.archive.events, key)
                self.ledger.archive_event_reads += final
                self.ledger.update_archive_reads += final
                self.ledger.update_work += final
                if self.name == "current_answer":
                    self.answers[key] = status_answer(frontier)
                else:
                    active = [entry for entry in frontier if entry[2] in VALUES]
                    if active:
                        self.witnesses[key] = active[0]
        elif self.name in (
            "certificate_partition",
            "proof_carrying_closed_cover",
            "counterexample_refined",
        ):
            self.current = {key: self.empty_frontier() for key in INITIAL_KEYS}
            indexed = self.name == "counterexample_refined"
            for event in self.archive.events:
                if indexed:
                    self.posting_index.setdefault(event.key, []).append(event.seq - 1)
                    self.ledger.index_writes += 1
                    self.ledger.auxiliary_index_bytes = len(
                        canonical(self.posting_index).encode()
                    )
                if event.key in INITIAL_KEYS:
                    self.apply_event_to_frontiers(
                        self.current, event, indexed_repair=indexed
                    )
                    self.ledger.update_work += 1
                if indexed and event.seq in self.checkpoints:
                    for key in INITIAL_KEYS:
                        self.snapshots[(key, event.seq)] = self.current[key]
                        self.ledger.refinement_work += len(SOURCES)
                self.record_active_size()
        elif self.name == "rolling_exact_window":
            window: list[Event] = []
            for event in self.archive.events:
                window.append(event)
                self.ledger.update_work += 1
                if len(window) > WINDOW:
                    expired = window.pop(0)
                    self.apply_event_to_frontiers(
                        self.rolling_base,
                        expired,
                        indexed_repair=False,
                    )
                    self.rolling_base_boundary += 1
                    self.ledger.update_work += 1
                self.rolling_events = tuple(window)
                self.record_active_size()
        else:
            raise ValueError(self.name)
        self.record_active_size()

        # The event-by-event maintained states must agree with independent
        # direct replay at the final boundary.
        if self.name in (
            "certificate_partition",
            "proof_carrying_closed_cover",
            "counterexample_refined",
        ):
            expected = frontiers_at(self.archive, INITIAL_KEYS, final)
            require(self.current == expected, f"{self.name}: streaming current state")
            if self.name == "counterexample_refined":
                require(
                    self.posting_index == self.archive.postings,
                    "streaming posting index must equal independent full index",
                )
        if self.name == "rolling_exact_window":
            expected_base = frontiers_at(
                self.archive,
                all_keys(self.archive.events),
                self.rolling_base_boundary,
            )
            require(
                all(
                    self.rolling_base.get(key, self.empty_frontier()) == frontier
                    for key, frontier in expected_base.items()
                ),
                "rolling streaming base",
            )

    def local_frontier(self, query: Query) -> Frontier | None:
        final = len(self.archive.events)
        if self.name == "full_history_active":
            boundary = final if query.as_of is None else query.as_of
            self.ledger.local_state_reads += boundary
            return frontier_from_events(self.active_history[:boundary], query.key)
        if self.name in ("current_answer", "exact_witness", "full_replay"):
            return None
        if self.name == "rolling_exact_window":
            boundary = final if query.as_of is None else query.as_of
            if boundary < self.rolling_base_boundary:
                return None
            base = self.rolling_base.get(query.key, frontier_from_events((), query.key))
            self.ledger.local_state_reads += len(base)
            self.ledger.local_state_reads += boundary - self.rolling_base_boundary
            suffix = tuple(
                event
                for event in self.rolling_events[: boundary - self.rolling_base_boundary]
                if event.key == query.key
            )
            reconstructed = {entry[0]: entry for entry in base}
            for event in suffix:
                current = reconstructed[event.source]
                if event.operation == "INVALIDATE":
                    # A window invalidation of the currently represented base
                    # version needs an older version chain, which this rolling
                    # state deliberately does not retain.  Exact fallback is
                    # therefore mandatory in that case.
                    if current[1] == event.target_version:
                        return None
                    continue
                if event.operation == "RETRACT":
                    reconstructed[event.source] = (
                        event.source,
                        event.source_version,
                        RETRACT,
                        "",
                        event.seq,
                    )
                else:
                    reconstructed[event.source] = (
                        event.source,
                        event.source_version,
                        str(event.value),
                        event.exact_text,
                        event.seq,
                    )
            return tuple(reconstructed[source] for source in SOURCES)
        if query.as_of is None and query.key in self.current:
            self.ledger.local_state_reads += len(self.current[query.key])
            return self.current[query.key]
        if query.as_of is not None and (query.key, query.as_of) in self.snapshots:
            self.ledger.local_state_reads += len(
                self.snapshots[(query.key, query.as_of)]
            )
            return self.snapshots[(query.key, query.as_of)]
        return None

    def refine(self, query: Query, frontier: Frontier) -> None:
        if self.name != "counterexample_refined" or not query.refine_on_miss:
            return
        state_writes = 0
        if query.as_of is None:
            self.current[query.key] = frontier
            state_writes += len(frontier)
        else:
            self.snapshots[(query.key, query.as_of)] = frontier
            state_writes += len(frontier)
            has_later, index_reads = has_position_at_or_after(
                self.posting_index, query.key, query.as_of
            )
            self.ledger.index_entry_reads += index_reads
            self.ledger.query_index_reads += index_reads
            if not has_later:
                # The trusted posting directory proves that this temporal
                # frontier is also current, so one refinement discharges both
                # obligations without rereading the archive.
                self.current[query.key] = frontier
                state_writes += len(frontier)
        self.ledger.refinement_work += state_writes
        self.record_active_size()

    def query(self, query: Query) -> dict[str, object]:
        self.ledger.queries += 1
        expected_answer, expected_proof = independent_oracle(self.archive, query)

        # Answer-only and one-witness summaries explicitly attempt their
        # retained current state when applicable, but the contract requires a
        # complete three-source frontier.  The assertion gate blocks the
        # incomplete attempt before any assertion is emitted.
        partial_attempt = (
            query.as_of is None
            and (
                (self.name == "current_answer" and query.key in self.answers)
                or (self.name == "exact_witness" and query.key in self.witnesses)
            )
        )
        if partial_attempt:
            self.ledger.blocked_local_attempts += 1
            self.ledger.local_state_reads += 1

        frontier = self.local_frontier(query)
        source = "local"
        archive_reads = 0
        index_reads = 0
        trusted_frontier: Frontier
        if frontier is not None:
            answer = answer_from_frontier(query, frontier)
            boundary = len(self.archive.events) if query.as_of is None else query.as_of
            proof = certificate(
                query, frontier, answer, boundary, self.archive.digest()
            )
            if structural_gate(query, answer, proof, frontier, self.archive):
                self.ledger.local_hits += 1
                trusted_frontier = frontier
            else:
                self.ledger.blocked_local_attempts += 1
                frontier = None
        if frontier is None:
            if self.name == "full_replay":
                answer, proof, trusted_frontier, archive_reads, index_reads = oracle(
                    self.archive, query, "full"
                )
                self.ledger.primary_archive_queries += 1
                source = "primary_full_replay"
            elif self.name == "counterexample_refined":
                answer, proof, trusted_frontier, archive_reads, index_reads = oracle(
                    self.archive, query, "index", self.posting_index
                )
                self.ledger.fallbacks += 1
                source = "indexed_fallback"
                self.refine(query, trusted_frontier)
            else:
                answer, proof, trusted_frontier, archive_reads, index_reads = oracle(
                    self.archive, query, "full"
                )
                self.ledger.fallbacks += 1
                source = "exact_fallback"
            self.ledger.archive_event_reads += archive_reads
            self.ledger.query_archive_reads += archive_reads
            self.ledger.index_entry_reads += index_reads
            self.ledger.query_index_reads += index_reads

        gate = structural_gate(
            query, answer, proof, trusted_frontier, self.archive
        )
        self.ledger.verifier_entries_checked += len(SOURCES)
        answer_ok = answer == expected_answer
        proof_ok = proof == expected_proof
        supported = gate and answer_ok and proof_ok
        if not supported:
            self.ledger.unsupported_assertions += 1
        self.ledger.answer_errors += int(not answer_ok)
        self.ledger.justification_errors += int(not proof_ok or not gate)
        entries = proof["entries"]
        self.ledger.proof_entries_emitted += len(entries)
        self.ledger.proof_bytes_emitted += len(canonical(proof).encode())
        self.record_active_size()
        return {
            "strategy": self.name,
            "query_id": query.id,
            "source": source,
            "answer": answer,
            "certificate": proof,
            "archive_event_reads": archive_reads,
            "index_entry_reads": index_reads,
            "answer_ok": answer_ok,
            "justification_ok": proof_ok and gate,
            "unsupported_assertion": not supported,
        }


STRATEGIES = (
    "full_history_active",
    "full_replay",
    "current_answer",
    "exact_witness",
    "certificate_partition",
    "proof_carrying_closed_cover",
    "rolling_exact_window",
    "counterexample_refined",
)


def cover_comparison() -> dict[str, object]:
    return {
        "workload_accepted_output_relation": (
            "each exact frontier has one source/version/text-bound complete certificate"
        ),
        "workload_verdict": (
            "compatible proof blocks are frontier-equality blocks; the proof-carrying "
            "implementation is therefore an intentional operational alias of the "
            "certificate partition and has no overlap advantage"
        ),
        "separate_exact_fixture": "../../../proofs/general_contract_search_results.json",
        "separate_fixture_scope": (
            "the 3-state right-congruent partition versus 2-state shareable-proof "
            "closed-cover result is a separate finite theorem, not a workload measurement"
        ),
    }


def run() -> tuple[dict[str, object], list[dict[str, object]]]:
    events, checkpoints, queries = load_items()
    archive = Archive.build(events)
    raw_rows: list[dict[str, object]] = []
    strategy_reports: list[dict[str, object]] = []
    for name in STRATEGIES:
        strategy = StrategyState(name=name, archive=archive, checkpoints=checkpoints)
        strategy.initialize()
        for query in queries:
            raw_rows.append(strategy.query(query))
        ledger = strategy.ledger.payload()
        require(ledger["answer_errors"] == 0, f"{name}: answer error")
        require(ledger["justification_errors"] == 0, f"{name}: justification error")
        require(ledger["unsupported_assertions"] == 0, f"{name}: unsupported assertion")
        strategy_reports.append(
            {
                "strategy": name,
                "ledger": ledger,
                "notes": {
                    "proof_carrying_closed_cover": (
                        "no state advantage under version-bound proofs"
                        if name == "proof_carrying_closed_cover"
                        else None
                    )
                },
            }
        )

    by_name = {row["strategy"]: row["ledger"] for row in strategy_reports}
    demand = by_name["counterexample_refined"]
    rolling = by_name["rolling_exact_window"]
    archive_bytes = archive.event_bytes()
    demand_storage = demand["final_active_bytes"] + demand["auxiliary_index_bytes"]
    require(
        by_name["certificate_partition"]
        == by_name["proof_carrying_closed_cover"],
        "state-bound proof cover must equal the certificate partition",
    )
    require(demand["fallbacks"] <= 6, "frozen post-smoke fallback bound")
    require(demand["query_archive_reads"] <= 30, "frozen demand-refinement query-read bound")
    require(demand["archive_event_reads"] <= 40, "frozen demand-refinement total-read bound")
    require(demand["query_index_reads"] <= 60, "frozen demand-refinement query-index bound")
    require(demand["index_entry_reads"] <= 80, "frozen demand-refinement total-index bound")
    require(
        demand_storage < archive_bytes,
        "demand-refined active plus index bytes must remain below exact history bytes",
    )
    require(
        3 * demand_storage <= 2 * archive_bytes,
        "demand-refined active plus index storage must be at least one-third below history",
    )
    require(
        rolling["final_active_bytes"] < archive_bytes,
        "rolling active bytes must remain below exact history bytes",
    )
    require(
        by_name["full_history_active"]["final_active_bytes"] == archive_bytes,
        "full-history canonical byte baseline",
    )
    raw_rows_sha256 = hashlib.sha256(canonical(raw_rows).encode()).hexdigest()
    report = {
        "schema_version": 2,
        "evidence_label": "EXACT deterministic benchmark",
        "input_bindings": {
            "items_sha256": hashlib.sha256(ITEMS.read_bytes()).hexdigest(),
            "design_bounds_sha256": hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
            "implementation_sha256": hashlib.sha256(
                Path(__file__).read_bytes()
            ).hexdigest(),
            "raw_rows_sha256": raw_rows_sha256,
            "archive_sha256": archive.digest(),
        },
        "workload": {
            "events": len(events),
            "queries": len(queries),
            "sources": list(SOURCES),
            "keys_seen": list(all_keys(events)),
            "initial_compiled_keys": list(INITIAL_KEYS),
            "causal_checkpoints": list(checkpoints),
            "rolling_window": WINDOW,
            "common_archive_event_writes": len(events),
            "archive_bytes": archive_bytes,
            "stable_key_index_bytes": archive.index_bytes(),
            "active_byte_encoding": (
                "UTF-8 canonical JSON of each strategy's complete logical active payload; "
                "an implementation-specific serialization proxy, not entropy or an "
                "asymptotic state-complexity measure"
            ),
            "byte_comparison_status": (
                "IMPLEMENTATION ARTIFACT: fixed canonical JSON encodings only"
            ),
            "active_units_warning": (
                "logical units are type-specific diagnostics and are not compared across strategies"
            ),
        },
        "resource_ledger_model": {
            "scope": (
                "complete for the declared logical counters, not a total CPU, wall-clock, "
                "hashing, allocation, serialization, or cryptographic-work ledger"
            ),
            "archive_event_reads": "materialized archive event records inspected",
            "index_entry_reads": (
                "posting-directory selection, binary-search probes, and every returned posting"
            ),
            "index_writes": "one online posting insertion per ingested event",
            "update_work": "declared logical event/frontier operations, not machine instructions",
            "refinement_work": "frontier entries written into a newly cached snapshot",
            "active_bytes": (
                "canonical JSON payload bytes; auxiliary index bytes are separate and monotone, "
                "so their final value is their peak value in this workload"
            ),
        },
        "features": [
            "additions",
            "revisions",
            "retractions",
            "contradictory sources",
            "source-version invalidation",
            "delayed relevance",
            "exact wording",
            "temporal queries",
            "complete negative evidence",
            "new key obligations under a fixed query language",
        ],
        "strategies": strategy_reports,
        "proof_carrying_cover_comparison": cover_comparison(),
        "frozen_post_smoke_design_checks": {
            "evidence_label_is_not_preregistered": True,
            "all_strategies_zero_answer_error": True,
            "all_strategies_zero_complete_justification_error": True,
            "all_strategies_zero_unsupported_assertions": True,
            "demand_refined_fallbacks_at_most_6": demand["fallbacks"],
            "demand_refined_query_event_reads_at_most_30": demand[
                "query_archive_reads"
            ],
            "demand_refined_total_event_reads_at_most_40": demand[
                "archive_event_reads"
            ],
            "demand_refined_query_index_reads_at_most_60": demand[
                "query_index_reads"
            ],
            "demand_refined_total_index_reads_at_most_80": demand[
                "index_entry_reads"
            ],
            "demand_refined_active_plus_index_bytes": [
                demand_storage,
                archive_bytes,
            ],
            "implementation_encoding_storage_at_least_one_third_below_history": True,
            "rolling_active_bytes_below_history": [
                rolling["final_active_bytes"],
                archive_bytes,
            ],
        },
        "trust_boundary": (
            "archive immutability/root identity, stable-key index completeness, source-universe "
            "identity, and active-state integrity are trusted exact primitives. The assertion "
            "gate binds outputs to those primitives and the benchmark independently replays "
            "semantics, but no cryptographic membership/nonmembership proof is implemented"
        ),
        "scientific_verdict": (
            "The online-maintained strategy subset implements structured exact fast paths, "
            "charged invalidation repair, and exact fallback with a fixed canonical-encoding "
            "ledger. Two deliberately insufficient baselines are compiled by post-ingestion "
            "replay, and full replay keeps no active state. "
            "It does not establish architectural novelty, cryptographic soundness, or behavior "
            "under new-key activation followed by further ingestion, or under "
            "query-language extension."
        ),
    }
    report["canonical_sha256"] = hashlib.sha256(canonical(report).encode()).hexdigest()
    return report, raw_rows


def csv_text(report: dict[str, object]) -> str:
    output = io.StringIO()
    fields = ("strategy", *Ledger.__dataclass_fields__)
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in report["strategies"]:
        ledger = row["ledger"]
        writer.writerow({"strategy": row["strategy"], **{key: ledger[key] for key in fields[1:]}})
    return output.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report, raw = run()
    if args.write:
        RESULTS.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        RAW.write_text("".join(canonical(row) + "\n" for row in raw))
        SCORED.write_text(csv_text(report))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Infinite-context exact reference benchmark")
        print(
            f"  [ok] {report['workload']['events']} events, "
            f"{report['workload']['queries']} queries"
        )
        for row in report["strategies"]:
            ledger = row["ledger"]
            print(
                f"  [ok] {row['strategy']}: active={ledger['final_active_bytes']}B "
                f"fallback={ledger['fallbacks']} event-reads={ledger['archive_event_reads']} "
                f"index-reads={ledger['index_entry_reads']} "
                f"errors={ledger['answer_errors'] + ledger['justification_errors']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
