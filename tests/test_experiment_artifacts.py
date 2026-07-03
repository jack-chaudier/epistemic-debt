"""Integrity checks on committed experiment artifacts (and secret hygiene)."""
import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PILOTS = REPO / "experiments" / "grok-pilots" / "2026-07-03"

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".txt", ".log", ".toml", ".yml", ".yaml"}


def test_no_api_key_material_anywhere():
    leak = re.compile(r"xai-[A-Za-z0-9]{20,}")
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
