"""Pins the distill-parity preregistration (2026-07-08) — the frozen thresholds.

The prereg's evidentiary value is that P-DP-0..5 were fixed before any GPU/API spend. This test
fails loudly if the committed prereg is edited: a threshold, gate, sample size, or the campaign
reading changing after the freeze must be a visible, deliberate act, not a drift.
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DP = REPO / "experiments" / "distill-parity" / "2026-07-08"


def _prereg():
    return (DP / "prereg_distill_parity.md").read_text()


def test_plan_and_prereg_present():
    assert (DP / "PLAN.md").exists()
    assert (DP / "prereg_distill_parity.md").exists()


def test_frozen_prediction_thresholds():
    text = _prereg()
    # P-DP-0 parity precondition
    assert "|acc_V − acc_J| ≤ 0.05" in text
    assert "≥ 0.70 on both verdict sides" in text
    # P-DP-1 Δ separation
    assert "Δ_V − Δ_J ≥ 0.15" in text
    assert "non-overlapping Wilson 95% CIs" in text
    # P-DP-2 witness channel
    assert "≥ Student-V + 0.20" in text
    assert "≥ 2× Student-J" in text
    # P-DP-3a/3b shift arms
    assert "error_V − error_J ≥ 0.15" in text
    assert "≤ 0.05 on witness-present items" in text
    # P-DP-4 stays descriptive, P-DP-5 stays WHICH-lost-only
    assert "descriptive only" in text
    assert "WHICH-lost only" in text
    assert "NOT" in text and "stated on Δ" in text


def test_frozen_gates_and_sample_sizes():
    text = _prereg()
    assert "AUC ≥ 0.60" in text                      # G1 surface-leak audit
    assert "verdict accuracy ≥ 0.85" in text          # G2 teacher inclusion gate
    joined = " ".join(text.split())  # wrap-safe
    assert "the teacher's verdict AND its named deciding witness are both correct" in joined  # G3
    assert "50/50 APPROVED/DENIED" in text            # G4 class balance
    assert "≥ 200 lost-cell and ≥ 200 retained-cell" in text
    assert "250 GSM8K + 250 MMLU" in text
    assert "≥ 150 items" in text                      # Arm 3a
    assert "thinking mode pinned OFF" in text


def test_frozen_campaign_reading():
    text = _prereg()
    assert "P-DP-0 passes AND P-DP-1 AND P-DP-3a pass" in text
    assert "Negative branch (pre-committed)" in text
    assert "Conditional commitment" in text           # lens probe runs if headline passes
