"""Pins the headline numbers of the 2026-07-08/09 campaigns (distill-parity, sections,
forced-cot) so a re-score or accidental edit that moves a ledger claim fails loudly."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DP = REPO / "experiments" / "distill-parity" / "2026-07-08"
SEC = REPO / "experiments" / "sections" / "2026-07-09"
FC = REPO / "experiments" / "forced-cot" / "2026-07-09"


def test_distill_parity_headlines():
    r = json.loads((DP / "distill_parity_results.json").read_text())
    p = r["predictions"]
    assert r["campaign_reading"] == "VOID"
    assert p["P-DP-0"]["parity_gap"] == 0.0639 and not p["P-DP-0"]["passed"]
    assert p["P-DP-1"]["delta_V"] == 0.9804 and p["P-DP-1"]["delta_J"] == 0.6862
    assert p["P-DP-1"]["ci_sep"] is True
    assert p["P-DP-3a"]["gap"] == -0.0278 and not p["P-DP-3a"]["passed"]
    base = r["base_control_exploratory"]
    assert base["gsm8k"]["acc"] == 0.516 and base["gsm8k"]["tok_median"] == 147
    # raw artifacts present with expected sizes
    assert sum(1 for _ in open(DP / "responses_raw.jsonl")) == 25440
    assert sum(1 for _ in open(DP / "train_V.jsonl")) == 7272
    assert sum(1 for _ in open(DP / "train_J.jsonl")) == 7272


def test_sections_headlines():
    r = json.loads((SEC / "sections_results.json").read_text())
    assert r["campaign_reading"]["upheld"] is False
    assert r["models"]["haiku"]["section"] == "DENIED"
    assert r["models"]["haiku"]["forecast"]["sign_hit"] == 0.9605
    assert r["models"]["grok"]["section"] == "APPROVED"  # the artifact-type sign flip
    a = json.loads((SEC / "sections_cached_annex.json").read_text())
    assert a["p_sec_3c_compression"]["haiku"]["sign_hit"] == 0.9425
    assert a["p_sec_3c_compression"]["grok"]["sign_hit"] == 0.2292
    assert a["p_sec_3b_realdoc"]["haiku"]["sign_hit"] == 1.0
    assert a["p_sec_3b_realdoc"]["gpt"]["sign_hit"] == 1.0
    assert all(v["sign_consistent"] for v in a["p_sec_1d_sensitivity"].values())
    assert sum(1 for _ in open(SEC / "responses_raw.jsonl")) == 5040


def test_forced_cot_headlines():
    r = json.loads((FC / "forced_cot_results.json").read_text())
    p = r["predictions"]
    assert p["P-FC-1"]["verdict"] == "LATENT" and p["P-FC-1"]["sv_gsm8k_cot"] == 0.448
    assert p["P-FC-0"]["passed"] is True
    assert p["P-FC-2"]["passed"] is False           # section not prompt-overridable
    assert p["P-FC-3"]["passed_sv"] is True and p["P-FC-3"]["passed_sj"] is False
    assert r["models"]["sj"]["cap_cot"]["gsm8k"] == 0.204   # register non-neutrality
    assert r["models"]["base"]["abl_bare"]["approve"] == 0.8139
    lens = json.loads((FC / "lens_results.json").read_text())
    assert lens["sv"]["computed_but_outvoted"] == 16 and lens["sv"]["n"] == 60
    assert lens["sj"]["computed_but_outvoted"] == 0
    assert sum(1 for _ in open(FC / "responses_raw.jsonl")) == 4740


def test_preregs_present_and_frozen_markers():
    for d, name in ((DP, "prereg_distill_parity.md"), (SEC, "prereg_sections.md"),
                    (FC, "prereg_forced_cot.md")):
        text = (d / name).read_text()
        assert "freeze" in text.lower() or "frozen" in text.lower()
