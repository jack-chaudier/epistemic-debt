"""Pins the headline numbers of the 2026-07-09 length-clamped iterated-compaction campaign
("settlement, not interest") so a re-score or accidental edit that moves a ledger claim fails
loudly."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IC = REPO / "experiments" / "iterated-compaction-clamped" / "2026-07-09"


def test_clamped_headlines():
    r = json.loads((IC / "clamped_results.json").read_text())
    p = r["predictions_evaluated"]
    # P-RC-0 guard fails 3/3 (all misses over-length) -> headline inapplicable as frozen
    assert p["P-RC-0"]["grok"] == {"in_band_frac": 0.8719, "passed": False}
    assert p["P-RC-0"]["haiku"]["passed"] is False and p["P-RC-0"]["gpt"]["passed"] is False
    assert r["verdict"]["headline_applicable"] is False
    # P-RC-1 band criterion passes per-model 3/3: flat survival under the clamp
    d = p["P-RC-1"]["per_model_detail"]
    assert d["grok"]["S8_over_S2"] == 1.0 and d["grok"]["net_decay"] == 0.0
    assert d["haiku"]["S8_over_S2"] == 0.9852 and d["haiku"]["net_decay"] == 0.0148
    assert d["gpt"]["S8_over_S2"] == 1.0 and d["gpt"]["net_decay"] == 0.0
    assert all(d[m]["band_outcome"] == "pass" for m in ("grok", "haiku", "gpt"))
    assert all(d[m]["subcheck_all_rounds_ge_098"] for m in ("grok", "haiku", "gpt"))
    # P-RC-2: squeeze kills on cue but overshoots the frozen interval (dense-floor regime)
    assert p["P-RC-2"]["drop_hazard"] == 0.3021
    assert p["P-RC-2"]["outcome"] == "neither_overshoot"
    assert p["P-RC-2"]["guard_delta5_ge_015"] is True
    # state function, absorbing death, verdict persistence
    assert p["P-RC-3"]["passed"] and p["P-RC-4"]["passed"] and p["P-RC-5"]["passed"]
    assert all(v == 0.0 for v in p["P-RC-4"]["per_chain"].values())
    # artifact integrity + cost logged
    assert r["total_calls"] == 3887 and r["total_cost_usd"] == 1.3234
    assert sum(1 for _ in open(IC / "responses_raw.jsonl")) == 3887


def test_clamped_prereg_frozen_marker():
    text = (IC / "prereg_clamped.md").read_text()
    assert "FROZEN" in text
    assert "Pre-smoke amendments" in text  # A1-A9 dated before any API call
