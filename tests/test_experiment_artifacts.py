"""Integrity checks on committed experiment artifacts (and secret hygiene)."""
import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PILOTS = REPO / "experiments" / "grok-pilots" / "2026-07-03"

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".txt", ".log", ".toml", ".yml", ".yaml"}


def test_no_api_key_material_anywhere():
    leak = re.compile(r"xai-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}")
    offenders = []
    for path in REPO.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and ".git" not in path.parts:
            if leak.search(path.read_text(errors="ignore")):
                offenders.append(str(path.relative_to(REPO)))
    assert not offenders, f"API-key-shaped strings found in: {offenders}"


def test_v4_preregistered_results_present_and_consistent():
    results = json.loads((PILOTS / "v4" / "v4_results.json").read_text())
    assert results, "v4_results.json empty"
    with (PILOTS / "v4" / "scored.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 60, f"v4 scored.csv has {len(rows)} rows, expected 60"


def test_every_pilot_version_has_core_artifacts():
    for version in ("v1", "v2", "v3", "v4"):
        d = PILOTS / version
        assert (d / "items.jsonl").exists(), f"{version}: missing items.jsonl"
        assert (d / "responses_raw.jsonl").exists(), f"{version}: missing responses_raw.jsonl"
        assert list(d.glob("runner*.py")), f"{version}: missing runner script"


MULTI = REPO / "experiments" / "multimodel" / "2026-07-03"


def test_multimodel_campaign_artifacts_present():
    for phase, results in (("v5", "v5_results.json"), ("transfer", "transfer_results.json"),
                           ("manifest", "manifest_results.json"),
                           ("reasoning-reader", "reasoning_results.json"),
                           ("coarseness", "coarseness_results.json"),
                           ("gemini-micro", "gemini_micro_results.json")):
        d = MULTI / phase
        assert (d / "responses_raw.jsonl").exists(), f"{phase}: missing responses_raw.jsonl"
        assert list(d.glob("runner*.py")), f"{phase}: missing runner script"
        assert list(d.glob("prereg*.md")), f"{phase}: missing preregistration"
        assert json.loads((d / results).read_text()), f"{phase}: missing/empty {results}"


WITNESS = REPO / "experiments" / "witness-compaction" / "2026-07-03"


def test_witness_compaction_artifacts_present():
    for phase, results in (("valuedense", "valuedense_results.json"),
                           ("curve", "curve_results.json"),
                           ("recursive", "recursive_results.json"),
                           ("routing", "routing_results.json")):
        d = WITNESS / phase
        assert (d / "responses_raw.jsonl").exists(), f"{phase}: missing responses_raw.jsonl"
        assert list(d.glob("runner*.py")), f"{phase}: missing runner script"
        assert list(d.glob("prereg*.md")), f"{phase}: missing preregistration"
        res = json.loads((d / results).read_text())
        assert res, f"{phase}: missing/empty {results}"


def test_no_env_file_committed():
    # the repo rule is "no .env files in the tree"; keys live in a gitignored .env
    # locally but must never be tracked/committed
    import subprocess
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True).stdout
    offenders = [ln for ln in tracked.splitlines() if ln == ".env" or ln.endswith("/.env")]
    assert not offenders, f".env is tracked by git: {offenders}"


def test_v5_preregistered_results_consistent():
    res = json.loads((MULTI / "v5" / "v5_results.json").read_text())
    per = res["per_model"]
    # confirmatory arms are complete (60 items each) and every prediction has a verdict
    for alias in ("grok", "haiku", "gpt"):
        assert per[alias]["cells"]["n"] == 60, f"{alias}: incomplete run"
        for p in per[alias]["preds"].values():
            assert isinstance(p["passed"], bool)
    # the gemini arm never becomes confirmatory silently
    assert "gemlite" not in per or per["gemlite"]["cells"]["n"] < 60 \
        or per["gemlite"]["applicable"] in (True, False)


RESCORE = REPO / "experiments" / "rescore" / "2026-07-06"


def test_rescore_campaign_artifacts_and_corrected_cells():
    for f in ("reparse.py", "judge.py", "judge_raw.jsonl", "adjudications.json",
              "reparse_results.json", "judge_results.json", "rescore_results.json",
              "routing_reanalysis.json", "recursive_reanalysis.json", "README.md"):
        assert (RESCORE / f).exists(), f"rescore: missing {f}"
    judge = json.loads((RESCORE / "judge_results.json").read_text())
    # judge instrument validity bar (fixed in the rescore README before the run)
    assert judge["summary"]["agreement"] >= 0.85
    assert judge["summary"]["unresolved"] == 0
    # the corrected phenotype cells: strong incoherence grok/gpt, missing-data haiku
    cells = judge["cells"]
    assert cells["v5/grok/which/lost"]["strong_incoherent"] == 16
    assert cells["v5/gpt/which/lost"]["strong_incoherent"] == 24
    assert cells["v5/haiku/which/lost"]["none_missing"] == 15
    assert cells["v5/haiku/which/lost"]["strong_incoherent"] <= 4
    # correctness conjuncts unaffected by the parser fix (WHICH-lost ~ 0)
    for m in ("grok", "haiku"):
        assert cells[f"v5/{m}/which/lost"]["correct"] == 0
    # ledger router re-analysis: recall 1.0, end-to-end 30/30
    routing = json.loads((RESCORE / "routing_reanalysis.json").read_text())
    assert routing["C_ledger_sim"]["recall"] == 1.0
    assert routing["C_ledger_sim"]["end_to_end"] == "30/30"


BUDGETLINE = REPO / "experiments" / "laws" / "2026-07-03" / "budgetline"


def test_budgetline_refutation_artifacts_consistent():
    for f in ("prereg_budgetline.md", "runner_budgetline.py", "items_clinical.jsonl",
              "responses_raw.jsonl", "scored.csv", "budgetline_results.json",
              "dualparser_results.json", "README.md"):
        assert (BUDGETLINE / f).exists(), f"budgetline: missing {f}"
    res = json.loads((BUDGETLINE / "budgetline_results.json").read_text())
    # the law's refutation must not silently flip: campaign fails, grok/clinical passes
    assert res["campaign"]["law_survives"] is False
    assert res["per_arm"]["grok/clinical"]["law_holds"] is True
    # every confirmatory arm ran all 7 budgets at n=30
    for arm in res["design"]["arms"]:
        assert all(v["n"] == 30 for v in res["per_arm"][arm]["curve"].values()), arm
    # the refutation is parser-robust (1/4 confirmatory arms under both parsers)
    dual = json.loads((BUDGETLINE / "dualparser_results.json").read_text())
    for parser in ("v1", "v2"):
        assert dual[f"{parser}/campaign"]["law_survives"] is False
        assert dual[f"{parser}/campaign"]["arms_passing"] == 1
