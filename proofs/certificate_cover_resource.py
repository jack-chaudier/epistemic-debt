#!/usr/bin/env python3
"""Exact accepted-output cover curves and transcript resource bounds.

For a fixed query, every complete output ``o`` (answer plus certificate) has an
acceptance fiber ``A_o`` of histories for which it is sound.  Define

    Gamma(C) = max |union_{o in S} A_o| over |S| <= C.

A deterministic protocol with at most C observable transcripts can be correct
without fallback on at most Gamma(C) histories: each transcript emits one
output and its history fiber must lie inside that output's acceptance fiber.
In the adaptive cell-probe model used by ``certificate_access_tradeoff.py``,
``b`` active bits and ``t`` probes returning ``w`` bits give at most
``C=2^(b+t*w)`` transcripts.  Restricting the curve to outputs whose proof
components fit a size budget makes the coverage bound certificate-specific,
but does not model verifier work or prove that a compact proof is locally
checkable.

The same argument is distributional after replacing cardinality by probability
mass, and it applies pointwise to fixed random coins.  It is a generalization of
the earlier disjoint-output counting bound, not a claim of a new communication-
complexity technique.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence


RESULTS = Path(__file__).with_name("certificate_cover_resource_results.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


@dataclass(frozen=True)
class AcceptedOutput:
    name: str
    histories: frozenset[int]
    proof_bits: int


def validate_outputs(
    history_count: int, outputs: Sequence[AcceptedOutput]
) -> None:
    require(history_count >= 0, "negative history count")
    for output in outputs:
        require(output.proof_bits >= 0, "negative proof size")
        require(
            all(0 <= history < history_count for history in output.histories),
            "accepted-output fiber outside history universe",
        )


def union_mask(outputs: Sequence[AcceptedOutput], chosen: Iterable[int]) -> int:
    mask = 0
    for index in chosen:
        for history in outputs[index].histories:
            mask |= 1 << history
    return mask


def cover_curve_combinations(
    history_count: int,
    outputs: Sequence[AcceptedOutput],
    proof_budget: int | None = None,
) -> tuple[int, ...]:
    validate_outputs(history_count, outputs)
    eligible = tuple(
        index
        for index, output in enumerate(outputs)
        if proof_budget is None or output.proof_bits <= proof_budget
    )
    curve = [0]
    for capacity in range(1, len(eligible) + 1):
        best = 0
        for size in range(capacity + 1):
            for chosen in itertools.combinations(eligible, size):
                best = max(best, union_mask(outputs, chosen).bit_count())
        curve.append(best)
    require(all(value <= history_count for value in curve), "cover exceeds universe")
    return tuple(curve)


def cover_curve_dynamic(
    history_count: int,
    outputs: Sequence[AcceptedOutput],
    proof_budget: int | None = None,
) -> tuple[int, ...]:
    """Independent subset-DP implementation of the same curve."""

    validate_outputs(history_count, outputs)
    masks = []
    for output in outputs:
        if proof_budget is None or output.proof_bits <= proof_budget:
            masks.append(sum(1 << history for history in output.histories))
    curve = [0]
    layers = [{0}]
    for mask in masks:
        updated = [set(layer) for layer in layers]
        updated.append(set())
        for used in range(len(layers) - 1, -1, -1):
            updated[used + 1].update(value | mask for value in layers[used])
        layers = updated
    cumulative = {0}
    for capacity in range(1, len(masks) + 1):
        cumulative.update(layers[capacity])
        curve.append(max(value.bit_count() for value in cumulative))
    require(all(value <= history_count for value in curve), "DP cover exceeds universe")
    return tuple(curve)


def weighted_cover_curve(
    weights: Sequence[Fraction],
    outputs: Sequence[AcceptedOutput],
    proof_budget: int | None = None,
) -> tuple[Fraction, ...]:
    validate_outputs(len(weights), outputs)
    require(sum(weights) == 1, "weights must form a probability distribution")
    require(all(weight >= 0 for weight in weights), "negative probability weight")
    eligible = tuple(
        index
        for index, output in enumerate(outputs)
        if proof_budget is None or output.proof_bits <= proof_budget
    )
    curve = [Fraction(0)]
    for capacity in range(1, len(eligible) + 1):
        best = Fraction(0)
        for size in range(capacity + 1):
            for chosen in itertools.combinations(eligible, size):
                covered = union_mask(outputs, chosen)
                mass = sum(
                    weight
                    for history, weight in enumerate(weights)
                    if covered & (1 << history)
                )
                best = max(best, mass)
        curve.append(best)
    return tuple(curve)


def minimum_transcript_bits(curve: Sequence[int], target: int) -> int | None:
    require(target >= 0, "negative target")
    if target == 0:
        return 0
    for bits in range(0, 64):
        capacity = min(1 << bits, len(curve) - 1)
        if curve[capacity] >= target:
            return bits
    return None


def set_partitions(size: int):
    blocks: list[int] = []

    def walk(element: int):
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


def compatible_cover_number(
    subset: int,
    outputs: Sequence[AcceptedOutput],
) -> int:
    """Minimum accepted-output fibers needed to cover one history subset."""

    if subset == 0:
        return 0
    masks = tuple(
        sum(1 << history for history in output.histories) & subset
        for output in outputs
    )
    for count in range(1, len(masks) + 1):
        for chosen in itertools.combinations(range(len(masks)), count):
            union = 0
            for index in chosen:
                union |= masks[index]
            if union == subset:
                return count
    raise RuntimeError("accepted outputs do not cover the requested history subset")


def simultaneous_active_minimum(
    history_count: int,
    queries: Sequence[Sequence[AcceptedOutput]],
    transcript_capacities: Sequence[int],
) -> tuple[int, tuple[tuple[int, ...], ...]]:
    """Exact cover-relaxed frontier for alternative future queries.

    This assumes an ideal transcript oracle can select any accepted-output
    fiber in a cover.  A concrete archive/probe decision tree may require more
    state or reads.
    """

    require(len(queries) == len(transcript_capacities), "query/capacity arity")
    valid: list[tuple[int, ...]] = []
    for partition in set_partitions(history_count):
        if all(
            compatible_cover_number(block, outputs) <= capacity
            for block in partition
            for outputs, capacity in zip(queries, transcript_capacities)
        ):
            valid.append(partition)
    require(bool(valid), "no simultaneous active partition")
    minimum = min(map(len, valid))
    minima = tuple(sorted(partition for partition in valid if len(partition) == minimum))
    return minimum, minima


def exhaustive_hypergraph_crosscheck(max_histories: int = 4) -> dict[str, int]:
    families = 0
    curves = 0
    for history_count in range(1, max_histories + 1):
        nonempty_fibers = tuple(range(1, 1 << history_count))
        for output_count in range(1, min(3, len(nonempty_fibers)) + 1):
            for family in itertools.combinations(nonempty_fibers, output_count):
                outputs = tuple(
                    AcceptedOutput(
                        name=f"o_{mask}",
                        histories=frozenset(
                            history
                            for history in range(history_count)
                            if mask & (1 << history)
                        ),
                        proof_bits=1,
                    )
                    for mask in family
                )
                left = cover_curve_combinations(history_count, outputs)
                right = cover_curve_dynamic(history_count, outputs)
                require(left == right, "independent cover-curve disagreement")
                families += 1
                curves += len(left)
    return {
        "maximum_histories": max_histories,
        "acceptance_hypergraphs": families,
        "curve_entries": curves,
    }


def examples() -> list[dict[str, object]]:
    cases: list[tuple[str, int, tuple[AcceptedOutput, ...], int | None]] = []
    identity = tuple(
        AcceptedOutput(f"history_{history}", frozenset({history}), 3)
        for history in range(8)
    )
    cases.append(("history_identifying", 8, identity, None))
    parity = (
        AcceptedOutput("even", frozenset({0, 2, 4, 6}), 1),
        AcceptedOutput("odd", frozenset({1, 3, 5, 7}), 1),
    )
    cases.append(("noninjective_answer", 8, parity, None))
    overlap = (
        AcceptedOutput("alpha", frozenset({0, 1}), 1),
        AcceptedOutput("beta", frozenset({1, 2}), 1),
    )
    cases.append(("overlapping_certificates", 3, overlap, None))
    proof_limited = (
        AcceptedOutput("short_left", frozenset({0, 1, 2}), 1),
        AcceptedOutput("short_right", frozenset({3, 4}), 1),
        AcceptedOutput("long_universal", frozenset(range(6)), 4),
    )
    cases.append(("proof_component_unrestricted", 6, proof_limited, None))
    cases.append(("proof_component_budget_one_bit", 6, proof_limited, 1))

    reports: list[dict[str, object]] = []
    for name, history_count, outputs, budget in cases:
        curve = cover_curve_combinations(history_count, outputs, budget)
        require(curve == cover_curve_dynamic(history_count, outputs, budget), name)
        uniform = tuple(Fraction(1, history_count) for _ in range(history_count))
        weighted = weighted_cover_curve(uniform, outputs, budget)
        reports.append(
            {
                "name": name,
                "histories": history_count,
                "eligible_outputs": sum(
                    budget is None or output.proof_bits <= budget for output in outputs
                ),
                "eligible_proof_component_bits": budget,
                "gamma": list(curve),
                "uniform_gamma": [
                    {"numerator": value.numerator, "denominator": value.denominator}
                    for value in weighted
                ],
                "bits_for_full_nonfallback_correctness": minimum_transcript_bits(
                    curve, history_count
                ),
            }
        )
    return reports


def simultaneous_query_example() -> dict[str, object]:
    history_count = 4
    first_bit = (
        AcceptedOutput("first_0", frozenset({0, 1}), 1),
        AcceptedOutput("first_1", frozenset({2, 3}), 1),
    )
    second_bit = (
        AcceptedOutput("second_0", frozenset({0, 2}), 1),
        AcceptedOutput("second_1", frozenset({1, 3}), 1),
    )
    queries = (first_bit, second_bit)
    minimum, minima = simultaneous_active_minimum(history_count, queries, (1, 1))
    require(minimum == 4, "simultaneous cross-query partition bound")
    return {
        "histories": history_count,
        "queries": 2,
        "query_geometry": "two crossing binary answer partitions",
        "transcripts_per_query_inside_active_state": [1, 1],
        "single_query_minimum_active_states": [2, 2],
        "minimum_active_states": minimum,
        "minimum_partition_count": len(minima),
        "lesson": (
            "one retained partition must refine both alternative-query geometries; "
            "this is a static necessary bound, not an online realization theorem"
        ),
    }


def build_report() -> dict[str, object]:
    crosscheck = exhaustive_hypergraph_crosscheck()
    rows = examples()
    by_name = {row["name"]: row for row in rows}
    require(by_name["history_identifying"]["gamma"] == list(range(9)), "identity curve")
    require(by_name["noninjective_answer"]["gamma"] == [0, 4, 8], "parity curve")
    require(
        by_name["proof_component_unrestricted"]["gamma"][1] == 6
        and by_name["proof_component_budget_one_bit"]["gamma"][1] == 3,
        "proof-component eligibility budget must change the curve",
    )
    report = {
        "schema_version": 1,
        "evidence_label": "THEOREM plus EXACT finite crosscheck",
        "scope": {
            "query": "fixed query per inequality; take the maximum requirement over query families",
            "protocol": "deterministic adaptive probes; randomized bound holds after fixing coins",
            "addresses": "probe addresses are determined by active state, query, and prior cell contents",
            "fallback_error": (
                "for one fixed deterministic query, F counts fallback histories and E counts "
                "the disjoint wrong-nonfallback histories; N-F-E must be positive"
            ),
            "finite_crosscheck": (
                "1-4 histories and 1-3 distinct nonempty acceptance fibers; annotations use "
                "uniform one-bit proof components"
            ),
        },
        "theorem": {
            "cardinality": "N-F-E <= Gamma_q(2^(b+t*w))",
            "distributional": "nonfallback correct mass <= Gamma_mu,q(2^(b+t*w))",
            "proof_component_size_eligibility": (
                "compute Gamma using only accepted outputs with proof_bits <= P; "
                "answer encoding length and verifier work are not bounded"
            ),
            "dormancy": "an old state fiber B needs no archive iff Gamma_q restricted to B at C=1 equals |B|",
        },
        "independent_crosscheck": crosscheck,
        "examples": rows,
        "simultaneous_abstract_cover_frontier": simultaneous_query_example(),
        "novelty_boundary": (
            "the proof is a transcript/cover counting argument related to certificate and "
            "nondeterministic cell-probe methods; novelty would require a new coupling to "
            "provenance proof generation or dynamic refinement cost"
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
    print("Accepted-output cover resource bound")
    print(
        "  [ok] independent finite curves: "
        f"{report['independent_crosscheck']['acceptance_hypergraphs']:,} hypergraphs"
    )
    for row in report["examples"]:
        print(f"  [ok] {row['name']}: Gamma={row['gamma']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
