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
    assert ids == list(range(1, 39))


def test_program_totals_match_public_surfaces():
    totals = json.loads((REPO / "results" / "program_totals.json").read_text())
    readme = (REPO / "README.md").read_text()
    site = (REPO / "site" / "index.html").read_text()
    assert f'{totals["headline_results"]}</b><span>headline results' in site
    assert f'{totals["api_calls"]:,} calls' in readme
    assert f'${totals["api_cost_usd"]:.2f} API' in readme
    assert f'${totals["total_cost_usd"]:.2f}' in readme
    assert f'${totals["total_cost_usd"]:.2f}</b>' in site
    all_calls_k = round((totals["api_calls"] + totals["local_calls_approx"]) / 1000)
    assert f'~{all_calls_k}k</b><span>LLM calls' in site


def test_public_metadata_matches_the_evidence_scope():
    site_head = (REPO / "site" / "index.html").read_text().split("</head>", 1)[0]
    assert "exact finite models" in site_head
    assert "preregistered LLM experiments" in site_head
    assert "exact laws" not in site_head
    assert "falsifiable laws" not in site_head


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
