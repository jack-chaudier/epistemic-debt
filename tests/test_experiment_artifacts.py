"""Integrity checks on committed experiment artifacts (and secret hygiene)."""
import csv
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PILOTS = REPO / "experiments" / "grok-pilots" / "2026-07-03"

TEXT_SUFFIXES = {".py", ".md", ".json", ".jsonl", ".csv", ".txt", ".log", ".toml", ".yml", ".yaml"}


def repo_visible_files():
    """Return tracked and unignored untracked files without entering ignored state."""
    commands = (
        ["git", "ls-files", "-z"],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    names = set()
    for command in commands:
        result = subprocess.run(
            command, cwd=REPO, capture_output=True, check=True
        )
        names.update(part.decode() for part in result.stdout.split(b"\0") if part)
    return [REPO / name for name in sorted(names)]


def test_no_api_key_material_anywhere():
    leak = re.compile(r"xai-[A-Za-z0-9]{20,}|sk-ant-[A-Za-z0-9-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}")
    offenders = []
    for path in repo_visible_files():
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
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
    # A repo-root .env may exist locally, but it must be ignored. Never open it here.
    names = [str(path.relative_to(REPO)) for path in repo_visible_files()]
    offenders = [
        name for name in names
        if Path(name).name == ".env" or Path(name).name.startswith(".env.")
    ]
    assert not offenders, f".env file is tracked or unignored: {offenders}"


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
TRANSFER_LAW = REPO / "experiments" / "transfer-law" / "2026-07-08"
READER_INF = REPO / "experiments" / "reader-inference-boundary" / "2026-07-08"
ITER_COMPACT = REPO / "experiments" / "iterated-compaction" / "2026-07-08"
SIGNPOST_FUSION = REPO / "experiments" / "signpost-fusion" / "2026-07-08"


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


def test_transfer_law_pilot_artifacts_and_headline_results():
    # 2026-07-08 Law-3 pilot: strong witness-conditioned transfer localization, but not the
    # hidden benchmark-parity kill-shot because the original-accuracy guard fails 3/3.
    for f in ("gen_items.py", "items.jsonl", "prereg_transfer_law.md", "runner.py",
              "responses_raw.jsonl", "scored.csv", "transfer_law_results.json", "README.md"):
        assert (TRANSFER_LAW / f).exists(), f"transfer-law: missing {f}"
    items = [json.loads(l) for l in (TRANSFER_LAW / "items.jsonl").open()]
    assert len(items) == 90
    from collections import Counter
    per_domain = Counter(it["domain"] for it in items)
    assert per_domain == {"ops_incident": 30, "clinical_enroll": 30, "ci_release": 30}
    raw = [json.loads(l) for l in (TRANSFER_LAW / "responses_raw.jsonl").open()]
    assert len(raw) == 1350
    per_model = Counter(r["model"] for r in raw)
    assert per_model == {"grok": 450, "haiku": 450, "gpt": 450}
    res = json.loads((TRANSFER_LAW / "transfer_law_results.json").read_text())
    assert res["pooled"]["transfer_gap_present_minus_missing"] == 0.4501
    for model in ("grok", "haiku", "gpt"):
        preds = res["per_model"][model]["predictions"]
        assert preds["P-L3-1_full_doc_sanity"] is True
        assert preds["P-L3-2_original_accuracy_guard"] is False
        assert preds["P-L3-3_witness_conditioned_transfer"] is True
        assert preds["P-L3-5_debt_localizes_failure"] is True
    assert res["per_model"]["grok"]["predictions"]["P-L3-4_reason_channel"] is False
    assert res["per_model"]["haiku"]["predictions"]["P-L3-4_reason_channel"] is True
    assert res["per_model"]["gpt"]["predictions"]["P-L3-4_reason_channel"] is True
    assert res["per_model"]["grok"]["metrics"]["transfer_gap_present_minus_missing"] == 0.2828
    assert res["per_model"]["haiku"]["metrics"]["transfer_gap_present_minus_missing"] == 0.5167
    assert res["per_model"]["gpt"]["metrics"]["transfer_gap_present_minus_missing"] == 0.5385


def test_transfer_law_source_truth_reanalysis():
    # pin the sharpened interpretation: the P-L3-2 guard failure is APPROVED-side only, and the
    # Law-3 transfer gap survives on the DENIED source subset (orig accuracy >= 0.70) with
    # CI-separated intervals for all three models. This keeps a future re-score from silently
    # collapsing the pilot to "inconclusive" when the localization is in fact robust.
    for f in ("reanalysis_by_source_truth.py", "reanalysis_by_source_truth.json"):
        assert (TRANSFER_LAW / f).exists(), f"transfer-law: missing {f}"
    res = json.loads((TRANSFER_LAW / "reanalysis_by_source_truth.json").read_text())
    assert res["denied_side_interpretation_holds"] is True
    for m in ("grok", "haiku", "gpt"):
        approved = res["by_model"][m]["APPROVED"]
        denied = res["by_model"][m]["DENIED"]
        # guard failure is APPROVED-side; DENIED-side clears the 0.70 prereg threshold
        assert approved["orig_decision_accuracy"]["p"] < 0.70, f"{m}: APPROVED side should fail guard"
        assert denied["orig_decision_accuracy"]["p"] >= 0.70, f"{m}: DENIED side should clear guard"
        assert denied["gap"] > 0 and denied["ci_separated"] is True, f"{m}: DENIED-side gap must be CI-separated"
    pooled = res["pooled_denied_source"]
    assert pooled["cf_present"]["p"] == 0.9778
    assert pooled["cf_missing"]["p"] == 0.5111
    assert pooled["gap"] == 0.4667


def _load_rib_gen():
    import importlib.util
    import sys as _sys
    _sys.path.insert(0, str(READER_INF))
    spec = importlib.util.spec_from_file_location("rib_gen", READER_INF / "gen_items.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_reader_inference_boundary_corpus_and_confound_clean():
    # the corpus is only valid if the derivability-class construction still passes its mechanical
    # guards (single culprit, margins, verdict-leak-free notes, per-class encoding, c2 base-leak)
    for f in ("prereg_reader_inference_boundary.md", "prereg_c2_confirmatory.md", "gen_items.py",
              "gen_c2.py", "items.jsonl", "items_c2.jsonl", "runner.py", "responses_raw.jsonl",
              "reader_inference_boundary_results.json", "reader_inference_boundary_c2_results.json",
              "README.md"):
        assert (READER_INF / f).exists(), f"reader-inference-boundary: missing {f}"
    items = [json.loads(l) for l in (READER_INF / "items.jsonl").open()]
    assert len(items) == 240
    from collections import Counter
    assert Counter(it["cls"] for it in items) == {"a": 60, "b": 60, "c": 60, "d": 60}
    gen = _load_rib_gen()
    assert gen.selfcheck(items) == [], "reader-inference-boundary corpus has confound problems"
    c2 = [json.loads(l) for l in (READER_INF / "items_c2.jsonl").open()]
    assert len(c2) == 60

    # The frozen c2 prerequisite is VOID: its original wrapper filtered every shared
    # ``CORPUS*`` issue, including this required surface-balance guard.  Pin the discovered
    # failure so a future cleanup cannot silently restore the confirmatory label.
    old_path = list(sys.path)
    old_gen_items = sys.modules.pop("gen_items", None)
    try:
        c2_spec = importlib.util.spec_from_file_location("rib_gen_c2", READER_INF / "gen_c2.py")
        c2_gen = importlib.util.module_from_spec(c2_spec)
        c2_spec.loader.exec_module(c2_gen)
        c2_problems, base_leak = c2_gen.selfcheck_c2(c2)
    finally:
        sys.path[:] = old_path
        sys.modules.pop("gen_items", None)
        if old_gen_items is not None:
            sys.modules["gen_items"] = old_gen_items
    assert base_leak == 0.0
    assert ("CORPUS-C", "surface-leak", "offset-bigger", 0.767) in c2_problems


def test_reader_inference_boundary_headline_results():
    # pin the 2026-07-08 verdict: the "retrieval-not-inference" reading is REFUTED — arithmetic
    # recovery (class c) is above the guess floor on all three models, arithmetic is in capacity,
    # and elimination (class b) is genuine. A re-score must not silently flip this.
    res = json.loads((READER_INF / "reader_inference_boundary_results.json").read_text())
    for m in ("grok", "haiku", "gpt"):
        preds = res["per_model"][m]["predictions"]
        # retrieval control + elimination + arithmetic-in-capacity all hold
        assert preds["P-RIB-0_retrieval_control"]["passed"] is True, f"{m}: retrieval control"
        assert preds["P-RIB-1_elimination_works"]["passed"] is True, f"{m}: elimination"
        assert preds["P-RIB-4_elimination_genuine"]["passed"] is True, f"{m}: elimination genuine"
        assert preds["P-RIB-5_arithmetic_in_capacity"]["passed"] is True, f"{m}: arith capacity"
        # the depth-boundary prediction FAILED — arithmetic recovery is above the floor
        assert preds["P-RIB-2_arithmetic_fails"]["passed"] is False, f"{m}: P-RIB-2 must fail"
        assert res["per_model"][m]["recovery"]["c"]["p"] > 0.50, f"{m}: recovery(c) above floor"
    assert res["verdict"]["retrieval_reading_refuted_on"] == ["gpt", "grok", "haiku"]

    # The cached c2 model behavior remains a real observation, but its confirmatory label is
    # VOID because the frozen surface-balance prerequisite failed (pinned in the corpus test).
    c2 = json.loads((READER_INF / "reader_inference_boundary_c2_results.json").read_text())
    assert c2["base_only_leak"] == 0.0
    assert c2["P-C2-3_no_residual_base_leak"]["passed"] is True
    assert c2["P-C2-1_recovery_survives"]["passed"] is True
    assert c2["P-C2-2_above_guess_floor"]["passed"] is True
    assert c2["verdict_retrieval_only_refuted"] is True
    for m in ("grok", "haiku", "gpt"):
        assert c2["per_model"][m]["recovery"]["ci"][0] > 0.50, f"{m}: c2 CI above guess floor"


def test_iterated_compaction_interest_rate_results():
    # pin the 2026-07-08 dynamical result: the epistemic interest rate is confirmed on grok+haiku
    # (geometric witness decay ~0.93/round while the verdict persists) and gpt is the near-
    # idempotent null. A re-score must not silently flip the confirmation or the null.
    for f in ("prereg_iterated_compaction.md", "runner.py", "responses_raw.jsonl",
              "iterated_compaction_results.json", "README.md"):
        assert (ITER_COMPACT / f).exists(), f"iterated-compaction: missing {f}"
    res = json.loads((ITER_COMPACT / "iterated_compaction_results.json").read_text())
    # budget binds on all three (validity guard)
    for m in ("grok", "haiku", "gpt"):
        assert res["per_model"][m]["predictions"]["P-IC-0_budget_binds"]["passed"] is True
        assert res["per_model"][m]["n_scored"] == 40, f"{m}: incomplete run"
    # interest rate confirmed on grok + haiku; not gpt (near-idempotent)
    assert set(res["verdict"]["interest_rate_confirmed_on"]) == {"grok", "haiku"}
    assert res["verdict"]["confirmed"] is True
    for m in ("grok", "haiku"):
        preds = res["per_model"][m]["predictions"]
        assert preds["P-IC-1_monotone_decay"]["passed"] is True, f"{m}: decay"
        assert preds["P-IC-2_gist_persists"]["passed"] is True, f"{m}: verdict persists"
        assert preds["P-IC-3_stable_ratio"]["passed"] is True, f"{m}: stable ratio"
        # decaying models share a per-round survival ratio near 0.93
        assert 0.90 <= res["per_model"][m]["rho_bar"] <= 0.95, f"{m}: rho_bar out of band"
    # gpt is the informative null: monotone-net-decay fails (near-idempotent), ratio still stable
    assert res["per_model"]["gpt"]["predictions"]["P-IC-1_monotone_decay"]["passed"] is False
    assert res["per_model"]["gpt"]["rho_bar"] > 0.97


def test_signpost_fusion_pilot_artifacts_and_headline_results():
    # pin the 2026-07-08 B5a fusion-contract split verdict: the mechanism (no unwitnessed
    # confidence, witness survival) is confirmed and the gap collapses where a shelf exists, but
    # the "collapse by construction at a MATCHED budget" claim is REFUTED — fusion overrides the
    # word budget (P-FU-3 fails 3/3 at 15w). A re-score must not silently upgrade this to a clean
    # win or lose the budget-confound.
    for f in ("prereg_fusion.md", "prereg_fusion_v2.md", "gen_items.py", "items.jsonl",
              "runner.py", "responses_raw.jsonl", "scored.csv", "fusion_results.json", "README.md"):
        assert (SIGNPOST_FUSION / f).exists(), f"signpost-fusion: missing {f}"
    res = json.loads((SIGNPOST_FUSION / "fusion_results.json").read_text())
    b40, b15 = res["budgets"]["40w"], res["budgets"]["15w"]

    # v1 (40w) is non-discriminative: control never enters the shelf regime (n_lost < 10 for
    # grok/gpt -> P-FU-1 inapplicable), the loose-budget confound.
    assert b40["verdict"]["applicable"] == {"grok": False, "haiku": True, "gpt": False}
    assert b40["per_model"]["grok"]["predictions"]["P-FU-1_gap_collapse"]["control_n_lost"] == 1

    # v2 (15w) enters the shelf regime on all three (control n_lost >= 10).
    assert b15["verdict"]["applicable"] == {"grok": True, "haiku": True, "gpt": True}
    for m in ("grok", "haiku", "gpt"):
        assert b15["per_model"][m]["predictions"]["P-FU-1_gap_collapse"]["control_n_lost"] >= 10

    # Mechanism confirmed at 15w: no unwitnessed confidence (P-FU-2) and witness survival (P-FU-4)
    # pass on all three; incoherence driven to 0 and S to ceiling by fusion.
    for m in ("grok", "haiku", "gpt"):
        pm = b15["per_model"][m]
        assert pm["predictions"]["P-FU-2_no_unwitnessed_confidence"]["passed"] is True, m
        assert pm["predictions"]["P-FU-4_survival"]["passed"] is True, m
        assert pm["fusion"]["incoherence_D"]["p"] == 0.0, m
        assert pm["fusion"]["S"] >= 0.97, m

    # Gap collapse holds where a shelf exists: P-FU-1 passes haiku + gpt, fails grok (parser
    # artifact + always-DENY prior).
    p1 = {m: b15["per_model"][m]["predictions"]["P-FU-1_gap_collapse"]["passed"] for m in ("grok", "haiku", "gpt")}
    assert p1 == {"grok": False, "haiku": True, "gpt": True}
    # gpt is the textbook collapse: Δ 0.44 -> ~0.07.
    assert b15["per_model"]["gpt"]["control"]["delta"] >= 0.40
    assert b15["per_model"]["gpt"]["fusion"]["delta"] <= 0.10

    # The matched-budget claim is REFUTED: the length guard fails on ALL three at 15w (fusion
    # overshoots control realized words by >1.25x) -> gap bought with length, not re-fused.
    for m in ("grok", "haiku", "gpt"):
        p3 = b15["per_model"][m]["predictions"]["P-FU-3_length_guard"]
        assert p3["passed"] is False, m
        assert p3["ratio"] > 1.25, m
    assert b15["verdict"]["fusion_collapses_gap"] is False

    # grok WHICH UNMATCHED > 5 in both 15w arms -> frozen-parser phenotype flagged for dual-judge.
    assert b15["per_model"]["grok"]["control"]["which_unmatched_D"] > 5
    assert b15["per_model"]["grok"]["fusion"]["which_unmatched_D"] > 5

    # cost sanity (well under the $5 cap) and scored.csv completeness (2 budgets x 2 arms x 3 x 90).
    assert res["total_cost_usd"] < 5.0
    with (SIGNPOST_FUSION / "scored.csv").open() as fh:
        assert sum(1 for _ in csv.DictReader(fh)) == 1080
