"""Integrity checks on the real-document external-validity tier (experiments/realdoc/2026-07-08).

Structural + confound-guard checks that do not require API calls:
  - the semi-synthetic corpus regenerates deterministically from sources.jsonl and passes selfcheck
    (0 value-collision / verdict-leak / balance problems);
  - schema, verdict balance, source count, and candidate disclosure are as preregistered;
  - provenance (SOURCES.md) is present with public-domain NTSB source URLs.
Headline numbers are pinned once the confirmatory run has been scored (see the results-JSON block).
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RD = REPO / "experiments" / "realdoc" / "2026-07-08"


def _load_items():
    return [json.loads(l) for l in (RD / "items.jsonl").read_text().splitlines() if l.strip()]


def test_corpus_present_and_provenance():
    assert (RD / "sources.jsonl").exists(), "missing sources.jsonl"
    assert (RD / "items.jsonl").exists(), "missing items.jsonl"
    assert (RD / "gen_items.py").exists() and (RD / "runner.py").exists()
    assert list(RD.glob("prereg*.md")), "missing preregistration"
    src = SOURCES_TABLE = (RD / "SOURCES.md").read_text()
    assert "public domain" in src.lower() and "ntsb" in src.lower(), "SOURCES.md lacks provenance"
    assert src.count("data.ntsb.gov") >= 10, "SOURCES.md should list a URL per source"


def test_schema_balance_and_disclosure():
    items = _load_items()
    assert len(items) == 60, f"expected 60 items, got {len(items)}"
    n_app = sum(1 for it in items if it["truth"] == "APPROVED")
    assert n_app == 30, f"verdict imbalance: {n_app} APPROVED / {60 - n_app} DENIED"
    assert len({it["source_id"] for it in items}) == 12, "expected 12 distinct sources"
    for it in items:
        assert len(it["parameters"]) == 3 and all(p["policy"] for p in it["parameters"])
        assert 300 <= it["word_count"] <= 900, f"{it['id']} word_count {it['word_count']} out of range"
        # candidate disclosure: every policy param name appears in policy_text
        for p in it["parameters"]:
            assert p["name"] in it["policy_text"], f"{it['id']}: {p['name']} not disclosed"
        fails = [p for p in it["parameters"] if not p["passes"]]
        if it["truth"] == "DENIED":
            assert len(fails) == 1 and it["failing_param"] == fails[0]["name"]
        else:
            assert not fails


def test_regenerates_deterministically_and_selfcheck_clean():
    sys.path.insert(0, str(RD))
    import gen_items  # noqa: E402
    sources = [json.loads(l) for l in (RD / "sources.jsonl").read_text().splitlines() if l.strip()]
    regen = gen_items.gen_items(sources)
    committed = _load_items()
    assert [it["id"] for it in regen] == [it["id"] for it in committed]
    assert [it["document"] for it in regen] == [it["document"] for it in committed], \
        "items.jsonl is not reproducible from sources.jsonl at the frozen seed"
    assert gen_items.selfcheck(committed) == [], "selfcheck must be clean (0 confound problems)"


def test_injected_value_uniqueness_in_document():
    """The real-doc confound: each injected value must be the ONLY numeral in the document that
    string-survival matches (so retention cannot false-match a source-narrative number)."""
    sys.path.insert(0, str(REPO / "experiments" / "grok-pilots" / "2026-07-03" / "v3"))
    from runner3 import numbers, retained
    for it in _load_items():
        doc_nums = numbers(it["document"])
        for p in it["parameters"]:
            hits = sum(1 for x in doc_nums if retained(f"{x}", p["value"]))
            assert hits == 1, f"{it['id']}: value {p['value']} matches {hits} doc numerals (want 1)"


# ── confirmatory-run pins (filled in after scoring; skipped until the results JSON exists) ──
def test_results_json_consistent_if_present():
    rp = RD / "realdoc_results.json"
    if not rp.exists():
        import pytest
        pytest.skip("confirmatory run not yet scored")
    res = json.loads(rp.read_text())
    assert res["total_cost_usd"] <= 8.0, "over the $8 preregistered budget cap"
    assert set(res["per_model"]) == {"haiku", "gpt"}, "expected exactly haiku + gpt"
    for m, pm in res["per_model"].items():
        assert "control" in pm and "fusion" in pm
        preds = pm["predictions"]
        # regime guard satisfied and all four preregistered predictions pass on both models
        assert preds["applicable_regime_guard"]["applicable"], f"{m}: regime guard not satisfied"
        for k in ("P-RD-1_dissociation", "P-RD-2_incoherence", "P-RD-3_fusion_kills", "P-RD-4_survival"):
            assert preds[k]["passed"] is True, f"{m}: {k} did not pass"
        # headline: contract-blind compaction of real accident prose yields a content-free
        # crash->DENY reflex (APPROVED-side accuracy on the floor); fusion lifts witness survival.
        assert pm["control"]["decision_acc_A"] == 0.0, f"{m}: control decA expected 0.0"
        assert pm["control"]["S"] <= 0.05 and pm["fusion"]["S"] >= 0.60, f"{m}: S lift not reproduced"
        assert pm["fusion"]["J"] >= 0.60 > pm["control"]["J"], f"{m}: J recovery not reproduced"
