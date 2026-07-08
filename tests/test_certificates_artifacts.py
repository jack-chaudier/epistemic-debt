"""Integrity checks on the B1 certificate-compaction pilot artifacts (2026-07-08).

Pins the campaign's structure and headline numbers so a re-score or accidental edit that moves
them fails loudly. Numbers are frozen from the committed certificate_results.json.
"""
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CERT = REPO / "experiments" / "certificates" / "2026-07-08"


def test_certificate_core_artifacts_present():
    for name in ("gen_items.py", "runner.py", "items.jsonl", "responses_raw.jsonl",
                 "certificate_results.json", "scored.csv"):
        assert (CERT / name).exists(), f"missing {name}"
    assert list(CERT.glob("prereg*.md")), "missing preregistration"


def test_certificate_corpus_shape_and_selfcheck():
    items = [json.loads(l) for l in (CERT / "items.jsonl").open()]
    assert len(items) == 90, f"expected 90 items, got {len(items)}"
    assert sum(1 for it in items if it["truth"] == "DENIED") == 45
    assert sum(1 for it in items if it["truth"] == "APPROVED") == 45
    # the generator's mechanical confound guard must still pass on the committed corpus
    sys.path.insert(0, str(REPO / "experiments" / "lib"))
    import domains as D  # noqa: E402
    assert D.selfcheck(items) == [], "selfcheck found confounds in the committed corpus"


def test_certificate_results_consistent():
    res = json.loads((CERT / "certificate_results.json").read_text())
    assert res["design"]["n_items"] == 90
    assert res["design"]["arms"] == ["ctrl", "vd", "vda", "cert"]
    assert res["design"]["policy_aware"] == {"ctrl": False, "vd": False, "vda": True, "cert": True}
    # every model present carries all four arms and the five predictions
    for alias, pm in res["per_model"].items():
        assert set(pm["arms"]) == {"ctrl", "vd", "vda", "cert"}, alias
        assert set(pm["predictions"]) >= {
            "P-CE-1_certificate_quotient", "P-CE-1b_vs_blind_valuedense",
            "P-CE-2_abstention_calibrated", "P-CE-3_beats_control", "P-CE-4_word_economy"}, alias
    assert res["total_cost_usd"] <= 6.0, "over the $6 prereg cap"


def test_certificate_scored_csv_rowcount():
    with (CERT / "scored.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    n_models = len(json.loads((CERT / "certificate_results.json").read_text())["per_model"])
    assert len(rows) == 90 * 4 * n_models, f"scored.csv has {len(rows)} rows"


# ── headline number pins (frozen from the committed certificate_results.json) ──
def test_certificate_headline_numbers():
    res = json.loads((CERT / "certificate_results.json").read_text())
    pm = res["per_model"]
    assert set(pm) == {"grok", "haiku", "gpt"}
    for alias in pm:
        arms = pm[alias]["arms"]
        # certificate has the best justified accuracy of any arm, and it is near-ceiling
        assert arms["cert"]["J"] >= 0.95, (alias, arms["cert"]["J"])
        assert arms["cert"]["J"] == max(arms[a]["J"] for a in ("ctrl", "vd", "vda", "cert"))
        # P-CE-1b: certificate beats *blind* value-dense at fewer realized words
        assert arms["cert"]["realized_words"] < arms["vd"]["realized_words"], alias


def test_certificate_prediction_scorecard_frozen():
    """The prereg outcomes are load-bearing — pin the exact pass/fail pattern."""
    res = json.loads((CERT / "certificate_results.json").read_text())
    pred = {m: {k: v["passed"] for k, v in res["per_model"][m]["predictions"].items()}
            for m in res["per_model"]}
    expected = {
        "grok":  {"P-CE-1_certificate_quotient": False, "P-CE-1b_vs_blind_valuedense": True,
                  "P-CE-2_abstention_calibrated": False, "P-CE-3_beats_control": True,
                  "P-CE-4_word_economy": False},
        "haiku": {"P-CE-1_certificate_quotient": True, "P-CE-1b_vs_blind_valuedense": True,
                  "P-CE-2_abstention_calibrated": False, "P-CE-3_beats_control": True,
                  "P-CE-4_word_economy": True},
        "gpt":   {"P-CE-1_certificate_quotient": False, "P-CE-1b_vs_blind_valuedense": True,
                  "P-CE-2_abstention_calibrated": True, "P-CE-3_beats_control": True,
                  "P-CE-4_word_economy": False},
    }
    assert pred == expected, pred
