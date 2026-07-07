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


HIGHPOWER = REPO / "experiments" / "highpower" / "2026-07-06"
DOMAINS = REPO / "experiments" / "domains" / "2026-07-06"


def _load_domains_lib():
    import importlib.util
    spec = importlib.util.spec_from_file_location("domains_lib", REPO / "experiments" / "lib" / "domains.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_highpower_and_domain_corpora_setup_and_confound_clean():
    # the 2026-07-06 tier-1/2 corpora must exist, be the preregistered size, and — since the
    # confound guard is what makes them valid — still pass selfcheck against the current generator
    hp = [json.loads(l) for l in (HIGHPOWER / "items.jsonl").open()]
    assert len(hp) == 400 and sum(it["truth"] == "DENIED" for it in hp) == 200
    dm = [json.loads(l) for l in (DOMAINS / "items.jsonl").open()]
    assert len(dm) == 600
    from collections import Counter
    per_domain = Counter(it["domain"] for it in dm)
    assert len(per_domain) == 6 and all(v == 100 for v in per_domain.values())
    for prereg in (HIGHPOWER / "prereg_highpower.md", DOMAINS / "prereg_domains.md"):
        assert prereg.exists(), f"missing {prereg}"
    lib = _load_domains_lib()
    assert lib.selfcheck(hp) == [], "high-power corpus has confound problems"
    assert lib.selfcheck(dm) == [], "domain-battery corpus has confound problems"


def test_highpower_tier1_headline_results():
    # pin the 2026-07-06 Tier-1 verdict so a re-score can't silently move it:
    # P-H1/H2/H4 pass 3/3; P-H3 fails on haiku only (retained-cell over-abstention)
    res = json.loads((HIGHPOWER / "highpower_results.json").read_text())
    v0 = res["by_variant"]["0"]
    for m in ("grok", "haiku", "gpt"):
        preds = v0[m]["predictions"]
        assert preds["P-H1_dissociation"] is True, f"{m}: P-H1 must pass"
        assert preds["P-H2_verdict_survives"] is True, f"{m}: P-H2 must pass"
        assert preds["P-H4_confab_locus"] is True, f"{m}: P-H4 must pass"
    assert v0["grok"]["predictions"]["P-H3_abstain_detects"] is True
    assert v0["gpt"]["predictions"]["P-H3_abstain_detects"] is True
    assert v0["haiku"]["predictions"]["P-H3_abstain_detects"] is False, \
        "P-H3 is the informative fail on haiku (over-abstains in retained cell)"
    # verdict-survival now holds against near-chance priors on haiku and gpt (not just grok's
    # always-DENY prior) — guard the prior separation that makes P-H2 meaningful
    assert v0["gpt"]["metrics"]["nonotes_deny_rate"] < 0.65
    assert v0["haiku"]["metrics"]["nonotes_deny_rate"] < 0.65
    assert v0["grok"]["metrics"]["nonotes_deny_rate"] == 1.0
    # every DENIED cell fully populated (200 each) and the paraphrase arm stayed inapplicable
    for m in ("grok", "haiku", "gpt"):
        assert v0[m]["metrics"]["n_denied"] == 200, f"{m}: incomplete DENIED cell"
    assert res["by_variant"]["1"]["grok"]["metrics"]["fail_retention"] < 0.15, \
        "grok paraphrase arm must remain inapplicable (retention collapsed), not silently scored"


def test_domains_tier2_headline_results():
    # pin the 2026-07-06 Tier-2 verdict: P-D3 holds gpt/haiku, fails grok as-frozen (3/4);
    # P-D2 verdict-survival splits gpt/haiku 6/6 vs grok 1/6
    res = json.loads((DOMAINS / "domains_results.json").read_text())
    d3 = res["P_D3_generalizes"]
    assert d3["gpt"]["holds"] is True and d3["gpt"]["passed"] == 6
    assert d3["haiku"]["holds"] is True and d3["haiku"]["passed"] == 5
    assert d3["grok"]["holds"] is False and (d3["grok"]["applicable"], d3["grok"]["passed"]) == (4, 3), \
        "grok fails P-D3 on the frozen parser; the one fail is the disclosed abbreviation artifact"
    # the single frozen-parser fail that flips under semantic rescue
    assert res["cells"]["grok/clinical_enroll"]["P_D1"] is False
    domains = res["design"]["domains"]
    assert sum(res["cells"][f"gpt/{x}"]["P_D2"] for x in domains) == 6
    assert sum(res["cells"][f"haiku/{x}"]["P_D2"] for x in domains) == 6
    assert sum(res["cells"][f"grok/{x}"]["P_D2"] for x in domains) == 1, \
        "P-D2 split: grok loses the verdict in 5/6 domains (false-nominal gist beats its DENY prior)"
    # grok's verdict loss is not prior-driven — its no-notes prior is pure always-DENY everywhere
    for x in domains:
        assert res["cells"][f"grok/{x}"]["metrics"]["nonotes_deny_rate"] == 1.0
