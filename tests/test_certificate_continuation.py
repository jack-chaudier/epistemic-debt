"""Regression tests for the exact certificate-continuation research artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
PROOFS = REPO / "proofs"
sys.path.insert(0, str(PROOFS))
sys.path.insert(0, str(PROOFS / "vendor"))

import certificate_continuation as continuation  # noqa: E402
import certificate_congruence_counterexamples as counterexamples  # noqa: E402
import certificate_access_tradeoff as access_tradeoff  # noqa: E402
import certificate_priority_theorem as priority  # noqa: E402
import checkpoint_frontier_theorem as checkpoints  # noqa: E402
import versioned_memory_contract as versioned  # noqa: E402


@pytest.fixture(scope="module")
def report():
    # This invokes the independent executable and asserts exact agreement on
    # the facts implemented by both programs before returning.
    return continuation.build_report(compare_independent=True)


def test_e0_report_is_reproducible_and_independently_reproduced(report):
    frozen = json.loads(
        (PROOFS / "certificate_continuation_e0_results.json").read_text()
    )
    # JSON object keys are strings on disk; a few in-memory count maps use
    # integer keys before canonical serialization.
    assert json.loads(json.dumps(report, sort_keys=True)) == frozen
    assert report["evidence_label"] == "EXACT"
    assert report["independent_reproduction"]["status"] == "PASS"
    assert len(report["independent_reproduction"]["agreement_sha256"]) == 64


def test_e0_counts_masks_and_minimum_multiplicities(report):
    models = {model["label"]: model for model in report["models"]}
    expected = {
        "Q_(3,2)": {
            "counts": (54, 7, 5, 6, 6, 2),
            "masks": [1, 2, 4, 8, 48, 64],
            "static_optima": 2,
        },
        "Q_(4,2)": {
            "counts": (90, 8, 6, 7, 7, 2),
            "masks": [1, 2, 4, 8, 16, 96, 128],
            "static_optima": 2,
        },
        "Q_(5,3)": {
            "counts": (783, 13, 7, 9, 9, 6),
            "masks": [1, 2, 4, 8, 16, 32, 960, 3072, 4096],
            "static_optima": 24,
        },
    }
    for label, pinned in expected.items():
        model = models[label]
        counts = model["counts"]
        assert (
            counts["raw_states"],
            counts["probe_joint_rows"],
            counts["answer_quotient_states"],
            counts["static_minimum_certificate_states"],
            counts["right_minimum_certificate_states"],
            counts["right_minimum_partition_count"],
        ) == pinned["counts"]
        assert counts["static_minimum_partition_count"] == pinned["static_optima"]
        assert (
            model["partitions"]["reported_right_congruent_minimum"]["masks"]
            == pinned["masks"]
        )


def test_e0_checks_every_required_algebraic_and_certificate_property(report):
    for model in report["models"]:
        checks = model["checks"]
        for key in (
            "reported_masks_reproduced",
            "reported_common_certificate_valid",
            "reported_answer_consistent",
            "reported_right_congruent",
            "raw_composition_closed",
            "raw_composition_associative",
            "right_action_closed",
            "right_action_associative",
            "certificate_output_sound",
            "all_active_states_reachable_with_all_chunks",
            "all_active_states_reachable_with_depth_one_events",
        ):
            assert checks[key], (model["label"], key)

        # The compact active state is a right action under exact incoming
        # chunks.  It is not a binary quotient semigroup for independently
        # summarized operands; even the probe/full-witness row quotient has
        # hidden representative-dependent left transitions.
        assert not checks["reported_left_congruent"]
        assert not checks["reported_two_sided_congruent"]
        assert not checks["full_witness_rows_left_congruent"]
        assert model["counts"]["left_congruent_partition_count_on_probe_rows"] == 0
        assert model["counts"]["two_sided_partition_count_on_probe_rows"] == 0
        assert model["right_action"]["classes"]
        assert model["right_action"]["composition_table"]


def test_e0_pins_right_and_left_counterexamples(report):
    models = {model["label"]: model for model in report["models"]}
    q53 = models["Q_(5,3)"]
    failure = q53["counterexamples"]["lexicographic_static_minimum_right"]
    assert failure["source_block_mask"] == 576
    assert failure["continuation_raw_index"] == 1
    assert failure["continuation_state"] == {
        "depth": 0,
        "coordinates": [-1, -1, 0],
    }
    assert [item["source_row"] for item in failure["witnesses"]] == [6, 9]
    assert [item["destination_row"] for item in failure["witnesses"]] == [7, 8]

    for model in models.values():
        failure = model["counterexamples"]["reported_partition_left"]
        first, second = failure["witnesses"][:2]
        assert first["source_row"] == second["source_row"] == 0
        assert first["source_raw_index"] != second["source_raw_index"]
        assert first["destination_row"] != second["destination_row"]
        assert first["destination_block"] != second["destination_block"]


def test_priority_characterization_and_transition_formula():
    summaries = priority.verify_selector_characterization(max_p=4)
    assert [row["static_minimum_partitions"] for row in summaries] == [
        1,
        2,
        24,
        20_736,
    ]
    assert [row["right_congruent_minimum_partitions"] for row in summaries] == [
        1,
        2,
        6,
        24,
    ]
    assert priority.verify_raw_transition_formula(max_k=5, max_p=3) == 900_669
    assert [
        row["states"] for row in priority.verify_fixed_priority_two_sided_quotient()
    ] == [34, 55, 209]
    assert [
        row["add_delete_states"]
        for row in priority.verify_retraction_phase_transition(max_p=5)
    ] == [2, 4, 8, 16, 32]


def test_general_counterexamples_and_unbounded_static_online_gap():
    smallest = counterexamples.verify_monoid_gap()
    assert smallest["state_minimal"]
    assert (smallest["static_minimum_states"], smallest["right_minimum_states"]) == (
        2,
        3,
    )

    gap = counterexamples.verify_unbounded_gap(max_states=8)
    assert all(
        row["static_minimum"] == 2 and row["right_minimum"] == row["states"]
        for row in gap["checked_instances"]
    )

    compatibility = counterexamples.verify_nontransitive_compatibility()
    assert compatibility["global_intersection"] == []
    nonunique = counterexamples.verify_nonunique_minima()
    assert len(nonunique["minimum_partitions"]) == 2
    assert not nonunique["join_admissible"]
    cover_gap = counterexamples.verify_closed_cover_partition_gap()
    assert cover_gap["semantic_partition_minimum"] == 3
    assert cover_gap["projected_closed_cover_minimum"] == 2
    assert cover_gap["reachable_semantic_implementation_pairs"] == (
        (0, 0),
        (1, 0),
        (1, 1),
        (2, 1),
    )


def test_versioned_dynamic_contract_current_temporal_boundary():
    dynamic = versioned.build_report(max_horizon=3)
    assert dynamic["right_congruence"]["current"]
    assert dynamic["right_congruence"]["temporal"]
    rows = {row["horizon"]: row for row in dynamic["counts"]}
    assert (
        rows[3]["histories"],
        rows[3]["current_answer_states"],
        rows[3]["current_certificate_static_states"],
        rows[3]["current_certificate_right_states"],
        rows[3]["source_local_ledger_states"],
        rows[3]["temporal_answer_states"],
        rows[3]["temporal_certificate_static_states"],
    ) == (1_728, 15, 228, 228, 540, 173, 1_728)
    failure = dynamic["semantic_checks"]["answer_only_right_failure"]
    assert failure["destinations"] == ["UNKNOWN", "SUPPORTED"]
    retroactive = dynamic["semantic_checks"]["retroactive_checkpoint_failure"]
    assert retroactive["shared_current_frontier"]
    assert retroactive["separating_boundary"] == 1
    assert versioned.current_frontier_count_formula(4, 4) == 579
    assert versioned.source_local_ledger_count_formula(4, 4) == 2_835
    assert versioned.checkpoint_count_formula((1, 4), 4) == 2_736
    assert versioned.checkpoint_count_formula((2, 4), 4) == 4_356
    assert versioned.checkpoint_count_formula((1, 2, 4), 4) == 9_504
    assert versioned.checkpoint_count_formula((1, 2, 3, 4), 4) == 20_736
    horizon_three = {
        tuple(schedule["boundaries"]): schedule["states"]
        for schedule in dynamic["checkpoint_sweep"][3]["schedules"]
    }
    assert horizon_three == {
        (3,): 228,
        (1, 3): 792,
        (2, 3): 792,
        (1, 2, 3): 1_728,
    }


def test_archive_access_and_fallback_counting_bound():
    assert access_tradeoff.verify_exhaustive_transcript_core() == 6_661
    rows = access_tradeoff.versioned_boundary_rows(max_horizon=8)
    horizon_four = rows[3]
    assert horizon_four["current_states"] == 579
    assert horizon_four["current_bits"] == 10
    assert horizon_four["exact_histories"] == 20_736
    assert horizon_four["max_all_as_of_fast_correct_with_current_bits"] == 1_024
    assert horizon_four["minimum_all_as_of_fallback_fraction"] > 0.95


def test_independent_checkpoint_product_sweep():
    generic = checkpoints.verify_parameter_family(max_horizon=3)
    assert generic["schedules_checked"] == 72
    actual = checkpoints.verify_actual_contract_horizon_four()
    assert actual[(4,)] == 579
    assert actual[(1, 4)] == 2_736
    assert actual[(2, 4)] == 4_356
    assert actual[(1, 2, 4)] == 9_504
    assert actual[(1, 2, 3, 4)] == 20_736
