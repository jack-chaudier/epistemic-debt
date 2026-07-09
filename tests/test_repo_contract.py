"""Repository-level contracts for agent guidance and public research surfaces."""

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EVIDENCE_LABELS = {
    "THEOREM", "EXACT", "PREREGISTERED", "OBSERVED", "REFUTED", "CONJECTURE"
}
OUTCOME_MODIFIERS = {"VOID", "LATENT", "INAPPLICABLE", "SPLIT"}
CORE_MARKDOWN = (
    REPO / "README.md",
    REPO / "results" / "RESULTS.md",
    REPO / "theory" / "justification-gap-program.md",
    REPO / "theory" / "related-work-positioning.md",
    REPO / "LICENSING.md",
    REPO / "THIRD_PARTY_NOTICES.md",
    REPO / "experiments" / "certificates" / "2026-07-08" / "README.md",
)


def test_agent_instruction_copies_are_identical():
    assert (REPO / "AGENTS.md").read_bytes() == (REPO / "CLAUDE.md").read_bytes()


def test_evidence_vocabulary_is_explicit():
    agents = (REPO / "AGENTS.md").read_text()
    ledger_key = "\n".join((REPO / "results" / "RESULTS.md").read_text().splitlines()[:5])
    for label in EVIDENCE_LABELS | OUTCOME_MODIFIERS:
        assert label in agents, f"AGENTS.md does not define {label}"
        assert label in ledger_key, f"RESULTS.md status key does not define {label}"


def test_readme_result_ids_are_contiguous_and_ordered():
    ids = [
        int(match.group(1))
        for match in re.finditer(r"^\| (\d+) \|", (REPO / "README.md").read_text(), re.MULTILINE)
    ]
    assert ids and ids == list(range(1, ids[-1] + 1))


def test_program_totals_match_public_surfaces():
    totals = json.loads((REPO / "results" / "program_totals.json").read_text())
    readme = (REPO / "README.md").read_text()
    site = (REPO / "site" / "index.html").read_text()
    assert f'{totals["headline_results"]}</b><span>headline results' in site
    assert f'{totals["api_calls"]:,} calls' in readme
    assert f'${totals["api_cost_usd"]:.2f} API' in readme
    assert f'${totals["total_cost_usd"]:.2f}' in readme
    assert f'${totals["total_cost_usd"]:.2f}' in site
    all_calls_k = round((totals["api_calls"] + totals["local_calls_approx"]) / 1000)
    assert f'{all_calls_k:,},000 API and local-GPU calls' in site


def test_public_metadata_matches_the_evidence_scope():
    site_head = (REPO / "site" / "index.html").read_text().split("</head>", 1)[0]
    assert "exact finite models" in site_head
    assert "preregistered LLM experiments" in site_head
    assert "exact laws" not in site_head
    assert "falsifiable laws" not in site_head


def test_ownership_license_and_citation_surfaces_are_explicit():
    required = (
        "LICENSE",
        "LICENSES/CC-BY-4.0.txt",
        "LICENSES/MIT-GSM8K.txt",
        "LICENSES/MIT-MMLU.txt",
        "LICENSES/MIT-STARK.txt",
        "LICENSING.md",
        "NOTICE",
        "THIRD_PARTY_NOTICES.md",
        "CITATION.cff",
        "CITATION.bib",
    )
    for path in required:
        assert (REPO / path).is_file(), f"missing ownership surface: {path}"

    for path in ("LICENSES/MIT-GSM8K.txt", "LICENSES/MIT-MMLU.txt", "LICENSES/MIT-STARK.txt"):
        notice = (REPO / path).read_text()
        normalized = " ".join(notice.split())
        assert "Permission is hereby granted" in notice
        assert "included in all copies or substantial portions" in normalized

    scope = (REPO / "LICENSING.md").read_text()
    cff = (REPO / "CITATION.cff").read_text()
    site = (REPO / "site" / "index.html").read_text()
    assert "Copyright © 2026 Jack Gaffney" in scope
    assert "Apache-2.0" in scope and "CC-BY-4.0" in scope
    assert "original HTML, CSS, and JavaScript are Apache-2.0" in scope
    assert "family-names: Gaffney" in cff and "given-names: Jack" in cff
    assert "license-url:" in cff
    assert not re.search(r"^license:\s", cff, re.MULTILINE)
    assert "© 2026 Jack Gaffney" in site


def test_road_to_durable_context_stays_inside_the_evidence_boundary():
    site = (REPO / "site" / "index.html").read_text()
    forbidden = (
        "Immortal archive",
        "O(∞)",
        "fixed point is real",
        "no benchmark on earth",
        "nobody ships",
        "today nobody measures it",
        "every long-running AI system",
        "38.4× the debt it removes",
        "N=400 with ±0.05 confidence intervals",
    )
    for claim in forbidden:
        assert claim not in site
    required = (
        "bounded working-context system",
        "never silently asserts",
        "the integrated runtime is open",
        "finite preregistered horizons",
        "unsupported assertion rate",
        "s8/s2 endpoints",
    )
    for claim in required:
        assert claim in site.lower()


def test_quickstart_uses_canonical_uv_command():
    readme = (REPO / "README.md").read_text()
    assert "uv run --with pytest --no-project -- pytest tests/ -q" in readme
    assert "python3 -m pytest tests/ -q" not in readme


def test_project_codex_config_is_portable_and_key_free():
    config = (REPO / ".codex" / "config.toml").read_text()
    forbidden = ("api_key", "bearer_token", "mcp_servers", "/Users/", "model =")
    assert not any(token in config for token in forbidden)


def test_local_agent_state_is_not_tracked():
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert ".claude/settings.local.json" not in tracked


def test_core_relative_markdown_links_resolve():
    broken = []
    for document in CORE_MARKDOWN:
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text()):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean = target.strip("<>").split("#", 1)[0]
            if clean and not (document.parent / clean).exists():
                broken.append(f"{document.relative_to(REPO)} -> {target}")
    assert not broken, "broken relative Markdown links: " + "; ".join(broken)
