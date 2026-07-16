"""Regression tests for the exact Level-4 boundary search artifacts."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[1]
PROOFS = REPO / "proofs"
BENCHMARK = REPO / "experiments" / "infinite-context-reference" / "2026-07-09"
sys.path.insert(0, str(PROOFS))

import certificate_cover_resource as cover_resource  # noqa: E402
import certificate_verifier_hitting as verifier_hitting  # noqa: E402
import evolving_checkpoint_refinement as evolving  # noqa: E402
import general_contract_search as contract_search  # noqa: E402
import general_contract_search_naive as naive_search  # noqa: E402
import linear_obligation_rank as linear_rank  # noqa: E402


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def load_benchmark_runner():
    path = BENCHMARK / "runner.py"
    spec = importlib.util.spec_from_file_location("infinite_context_runner", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def reports():
    runner = load_benchmark_runner()
    benchmark_report, raw_rows = runner.run()
    return {
        "general_contract_search_results.json": contract_search.build_report(),
        "linear_obligation_rank_results.json": linear_rank.build_report(),
        "evolving_checkpoint_refinement_results.json": evolving.build_report(),
        "certificate_cover_resource_results.json": cover_resource.build_report(),
        "certificate_verifier_hitting_results.json": verifier_hitting.build_report(),
        "reference_results.json": benchmark_report,
        "benchmark_raw": raw_rows,
        "benchmark_runner": runner,
    }


def test_general_search_scopes_and_independent_minima(reports):
    report = reports["general_contract_search_results.json"]
    assert "opaque labels" in report["scope"]
    models = {model["name"]: model for model in report["models"]}

    shareable = models["shareable_proof_closed_cover"]
    proof = shareable["optimized"]["proof"]
    assert (proof["static_minimum_states"], proof["right_minimum_states"]) == (2, 3)
    assert proof["closed_cover_minimum_states"] == 2
    assert proof["two_sided_minimum_states"] is None
    assert proof["two_sided_status"].startswith("INAPPLICABLE")
    assert shareable["independent_crosscheck"]["status"] == "PASS"
    assert shareable["independent_crosscheck"]["crosschecked_fields"] == [
        "answer.closed_cover_minimum_states",
        "proof.closed_cover_minimum_states",
    ]

    state_bound = models["state_bound_proof_erases_cover_gap"]["optimized"]["proof"]
    assert state_bound["closed_cover_minimum_states"] == 3
    monoid = models["static_right_monoid_gap"]["optimized"]["proof"]
    assert (monoid["static_minimum_states"], monoid["right_minimum_states"]) == (2, 3)
    assert monoid["two_sided_minimum_states"] == 3


def test_independent_search_handles_zero_event_contract():
    payload = {
        "name": "one_state_no_events",
        "states": ["only"],
        "outputs": [{"id": "o", "answer": "a"}],
        "accepted_outputs": [["o"]],
        "transitions": [],
        "start": 0,
    }
    assert naive_search.solve(payload, "answer", 1)["minimum_states"] == 1
    assert naive_search.solve(payload, "proof", 1)["minimum_states"] == 1


def test_left_action_must_be_paired_and_commute():
    bad = contract_search.Contract(
        name="bad_left_action",
        states=("s0", "s1"),
        outputs=(contract_search.Output("o", "a"),),
        accepted_outputs=(frozenset({"o"}), frozenset({"o"})),
        transitions=((1, 1),),
        event_names=("right",),
        start=0,
        left_transitions=((0, 0),),
    )
    with pytest.raises(RuntimeError, match="do not commute"):
        bad.validate()

    incoherent_start = contract_search.Contract(
        name="incoherent_start",
        states=("s0", "s1"),
        outputs=(contract_search.Output("o", "a"),),
        accepted_outputs=(frozenset({"o"}), frozenset({"o"})),
        transitions=((1, 0),),
        event_names=("toggle",),
        start=0,
        left_transitions=((0, 1),),
    )
    with pytest.raises(RuntimeError, match="disagree at start"):
        incoherent_start.validate()

    duplicate_events = contract_search.Contract(
        name="duplicate_event_names",
        states=("s0", "s1"),
        outputs=(contract_search.Output("o", "a"),),
        accepted_outputs=(frozenset({"o"}), frozenset({"o"})),
        transitions=((0, 1), (1, 0)),
        event_names=("same", "same"),
        start=0,
    )
    with pytest.raises(RuntimeError, match="duplicate event name"):
        duplicate_events.validate()

    invalid_start = contract_search.Contract(
        name="invalid_start",
        states=("s0",),
        outputs=(contract_search.Output("o", "a"),),
        accepted_outputs=(frozenset({"o"}),),
        transitions=((0,),),
        event_names=("event",),
        start=9,
        left_transitions=((0,),),
    )
    with pytest.raises(RuntimeError, match="invalid start"):
        invalid_start.validate()


def test_linear_fixed_horizon_rank_and_refinement(reports):
    report = reports["linear_obligation_rank_results.json"]
    assert report["independent_crosscheck"]["matrix_pairs"] == 16_452
    assert "fixed-horizon" in report["scope"]
    final = report["phase_sweep"][-1]
    assert final["horizon"] == 16
    families = final["families"]
    assert families["constant_global_parity"]["rank_bits"] == 1
    assert families["logarithmic_power_of_two_points"]["rank_bits"] == 5
    assert families["sublinear_square_points"]["rank_bits"] == 4
    assert families["dense_fixed_windows_3"]["rank_bits"] == 14
    assert families["identity_points"]["rank_bits"] == 16
    assert linear_rank.family_row("sublinear_square_points", 16) == linear_rank.point_rows(
        16, (0, 3, 8, 15)
    )
    assert linear_rank.gf2_rank((0b011, 0b110, 0b101), 3) == 2
    with pytest.raises(RuntimeError, match="outside horizon"):
        linear_rank.point_rows(3, (position for position in (0, 3)))
    assert linear_rank.build_report(1)["phase_sweep"][-1]["families"][
        "dense_fixed_windows_3"
    ]["rank_bits"] == 0
    with pytest.raises(RuntimeError, match="must be positive"):
        linear_rank.build_report(0)


def test_causal_and_bounded_retroactive_exact_checks(reports):
    report = reports["evolving_checkpoint_refinement_results.json"]
    assert report["causal_crosscheck"]["history_schedule_pairs"] == 82_453
    assert report["rolling_window_crosscheck"]["answers_checked"] == 28_195
    assert report["causal_checkpoint_theorem"]["archive_probes_at_declaration"] == 0
    assert report["bounded_retroactivity_theorem"]["outside_window"].startswith(
        "not determined"
    )
    profiles = report["refinement_split_profiles"]
    assert profiles[0]["split_multiplicity_histogram"] == {"2": 4, "3": 8}
    assert profiles[1]["split_multiplicity_histogram"] == {"3": 120, "4": 108}
    with pytest.raises(RuntimeError, match="positive history prefix"):
        evolving.causal_segment_machine(((0, 0),), (0,), 1)
    with pytest.raises(RuntimeError, match="window width"):
        evolving.rolling_window_state(((0, 0),), 1, -1)


def test_accepted_output_coverage_and_scope(reports):
    report = reports["certificate_cover_resource_results.json"]
    assert report["independent_crosscheck"]["acceptance_hypergraphs"] == 646
    examples = {row["name"]: row for row in report["examples"]}
    assert examples["history_identifying"]["gamma"] == list(range(9))
    assert examples["noninjective_answer"]["gamma"] == [0, 4, 8]
    assert examples["overlapping_certificates"]["gamma"] == [0, 2, 3]
    assert examples["proof_component_unrestricted"]["gamma"][1] == 6
    assert examples["proof_component_budget_one_bit"]["gamma"][1] == 3
    frontier = report["simultaneous_abstract_cover_frontier"]
    assert frontier["single_query_minimum_active_states"] == [2, 2]
    assert frontier["minimum_active_states"] == 4
    assert "proof_component_size_eligibility" in report["theorem"]
    eligibility = report["theorem"]["proof_component_size_eligibility"]
    assert "answer encoding length" in eligibility and "verifier work" in eligibility


def test_complete_proof_system_hitting_characterization(reports):
    report = reports["certificate_verifier_hitting_results.json"]
    scope = report["scope"]
    assert "perfectly complete" in scope["completeness"]
    assert report["independent_crosscheck"] == {
        "maximum_width": 4,
        "validity_relations": 65_808,
        "valid_history_checks": 525_348,
    }
    for row in report["positive_negative_separation"]:
        assert row["all_zero_complete_negative_probes"] == row["archive_cells"]
        assert row["any_one_positive_witness_probes"] == 1


def test_reference_benchmark_gate_and_commensurate_ledger(reports):
    report = reports["reference_results.json"]
    rows = {row["strategy"]: row["ledger"] for row in report["strategies"]}
    assert len(reports["benchmark_raw"]) == 8 * 12
    for ledger in rows.values():
        assert ledger["answer_errors"] == 0
        assert ledger["justification_errors"] == 0
        assert ledger["unsupported_assertions"] == 0

    assert rows["full_history_active"]["final_active_bytes"] == 8_147
    assert rows["full_replay"]["archive_event_reads"] == 434
    rolling = rows["rolling_exact_window"]
    assert (rolling["final_active_bytes"], rolling["fallbacks"]) == (1_915, 4)
    assert (rolling["update_archive_reads"], rolling["query_archive_reads"]) == (25, 36)
    refined = rows["counterexample_refined"]
    assert (refined["final_active_bytes"], refined["auxiliary_index_bytes"]) == (
        1_861,
        197,
    )
    assert (refined["update_archive_reads"], refined["query_archive_reads"]) == (8, 20)
    assert (refined["update_index_reads"], refined["query_index_reads"]) == (12, 43)
    assert refined["index_writes"] == 50
    assert refined["refinement_work"] == 24
    assert "followed by further ingestion" in report["scientific_verdict"]
    assert all(len(value) == 64 for value in report["input_bindings"].values())


def test_reference_rejects_future_or_missing_invalidation_target(
    reports, tmp_path, monkeypatch
):
    runner = reports["benchmark_runner"]
    bad_items = tmp_path / "bad_items.jsonl"
    bad_items.write_text(
        canonical(
            {
                "type": "event",
                "source": "atlas",
                "key": "launch",
                "operation": "INVALIDATE",
                "target_version": 2,
            }
        )
        + "\n"
    )
    monkeypatch.setattr(runner, "ITEMS", bad_items)
    with pytest.raises(RuntimeError, match="earlier material source version"):
        runner.load_items()


@pytest.mark.parametrize(
    ("rows", "message"),
    (
        (({"type": "checkpoint", "boundary": 0},), "must be positive"),
        (
            (
                {
                    "type": "query",
                    "id": "early",
                    "key": "launch",
                    "mode": "status",
                    "as_of": None,
                    "source": None,
                    "refine_on_miss": False,
                },
                {
                    "type": "event",
                    "source": "atlas",
                    "key": "launch",
                    "operation": "SET",
                    "value": "+",
                    "exact_text": "late event",
                },
            ),
            "events after queries",
        ),
    ),
)
def test_reference_rejects_unsupported_item_order(reports, tmp_path, monkeypatch, rows, message):
    runner = reports["benchmark_runner"]
    bad_items = tmp_path / "bad_order.jsonl"
    bad_items.write_text("".join(canonical(row) + "\n" for row in rows))
    monkeypatch.setattr(runner, "ITEMS", bad_items)
    with pytest.raises(RuntimeError, match=message):
        runner.load_items()


def test_structural_gate_is_explicitly_trust_relative(reports):
    runner = reports["benchmark_runner"]
    events, _, queries = runner.load_items()
    archive = runner.Archive.build(events)
    query = queries[0]
    boundary = len(events) if query.as_of is None else query.as_of
    fake_frontier = tuple(
        (source, 0, runner.ABSENT, "", 0) for source in runner.SOURCES
    )
    fake_answer = runner.answer_from_frontier(query, fake_frontier)
    fake_proof = runner.certificate(
        query, fake_frontier, fake_answer, boundary, archive.digest()
    )
    assert runner.structural_gate(
        query, fake_answer, fake_proof, fake_frontier, archive
    )
    oracle_answer, oracle_proof = runner.independent_oracle(archive, query)
    assert (fake_answer, fake_proof) != (oracle_answer, oracle_proof)


def test_rolling_state_treats_unseen_base_key_as_implicit_absence(reports):
    runner = reports["benchmark_runner"]
    events = tuple(
        runner.Event(
            seq=index,
            source="atlas",
            key="base" if index < 7 else "late",
            source_version=index if index < 7 else 1,
            operation="SET",
            value="+",
            exact_text=f"event {index}",
        )
        for index in range(1, 8)
    )
    archive = runner.Archive.build(events)
    strategy = runner.StrategyState(
        name="rolling_exact_window", archive=archive, checkpoints=()
    )
    strategy.initialize()
    query = runner.Query(id="late", key="late", mode="status")
    assert strategy.local_frontier(query) == runner.frontier_from_events(events, "late")


def test_canonical_generated_artifacts_match_code(reports):
    for filename in (
        "general_contract_search_results.json",
        "linear_obligation_rank_results.json",
        "evolving_checkpoint_refinement_results.json",
        "certificate_cover_resource_results.json",
        "certificate_verifier_hitting_results.json",
    ):
        disk = json.loads((PROOFS / filename).read_text())
        assert disk == reports[filename], filename
        if "canonical_sha256" in disk:
            claimed = disk["canonical_sha256"]
            unhashed = {key: value for key, value in disk.items() if key != "canonical_sha256"}
            assert hashlib.sha256(canonical(unhashed).encode()).hexdigest() == claimed

    benchmark = json.loads((BENCHMARK / "reference_results.json").read_text())
    assert benchmark == reports["reference_results.json"]
    benchmark_claimed = benchmark["canonical_sha256"]
    benchmark_unhashed = {
        key: value for key, value in benchmark.items() if key != "canonical_sha256"
    }
    assert hashlib.sha256(canonical(benchmark_unhashed).encode()).hexdigest() == (
        benchmark_claimed
    )
    raw_lines = (BENCHMARK / "responses_raw.jsonl").read_text().splitlines()
    assert [json.loads(line) for line in raw_lines] == reports["benchmark_raw"]
    assert hashlib.sha256(canonical(reports["benchmark_raw"]).encode()).hexdigest() == (
        benchmark["input_bindings"]["raw_rows_sha256"]
    )

    with (BENCHMARK / "scored.csv").open(newline="") as handle:
        scored = list(csv.DictReader(handle))
    assert [row["strategy"] for row in scored] == [
        row["strategy"] for row in benchmark["strategies"]
    ]
    expected_columns = {"strategy", *reports["benchmark_runner"].Ledger.__dataclass_fields__}
    assert set(scored[0]) == expected_columns
    expected_ledgers = {
        row["strategy"]: row["ledger"] for row in benchmark["strategies"]
    }
    for row in scored:
        assert {
            field: row[field] for field in reports["benchmark_runner"].Ledger.__dataclass_fields__
        } == {
            field: str(value) for field, value in expected_ledgers[row["strategy"]].items()
        }


def test_assert_based_legacy_validators_refuse_optimized_python():
    for filename in (
        "certificate_priority_theorem.py",
        "versioned_memory_contract.py",
        "certificate_access_tradeoff.py",
        "checkpoint_frontier_theorem.py",
        "certificate_congruence_counterexamples.py",
    ):
        completed = subprocess.run(
            [sys.executable, "-O", str(PROOFS / filename)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode != 0
        assert "exact theorem checks require Python assertions" in completed.stderr
