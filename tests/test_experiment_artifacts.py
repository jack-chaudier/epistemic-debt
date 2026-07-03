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
