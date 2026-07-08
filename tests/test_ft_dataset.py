"""Regression test for the B4 calibrated-reader SFT dataset (experiments/ft-dataset/2026-07-08).

Pins committed counts + class balance, runs the mechanical selfcheck over the emitted files,
verifies the by-item split is disjoint, and confirms the probe strings match the deployed
dissociation protocol. Stdlib + pytest only; no API calls.
"""
import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DS = os.path.join(ROOT, "experiments", "ft-dataset", "2026-07-08")
TRAIN = os.path.join(DS, "dataset_train.jsonl")
EVAL = os.path.join(DS, "dataset_eval.jsonl")


def _load(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def _build_module():
    spec = importlib.util.spec_from_file_location(
        "ft_build", os.path.join(DS, "build_dataset.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def data():
    return _load(TRAIN), _load(EVAL)


def test_counts(data):
    train, ev = data
    assert len(train) == 5021
    assert len(ev) == 885
    assert len(train) + len(ev) == 5906


def test_class_balance(data):
    train, ev = data
    from collections import Counter
    c = Counter((r["meta"]["channel"], r["meta"]["klass"]) for r in train + ev)
    assert c[("decision", "CITED_DENIED")] == 967
    assert c[("decision", "CONFIRMED_APPROVED")] == 632
    assert c[("decision", "CONS_MISSING")] == 1354
    assert c[("which", "WHICH_CITED")] == 967
    assert c[("which", "WHICH_NONE_NO_FAILURE")] == 632
    assert c[("which", "WHICH_NONE_MISSING_DATA")] == 1354
    # NONE_NO_FAILURE must sit near the requested ~10% so the model learns the row-20 distinction
    nf = c[("which", "WHICH_NONE_NO_FAILURE")]
    assert 0.08 <= nf / len(train + ev) <= 0.13


def test_selfcheck_passes_on_committed_files(data):
    train, ev = data
    mod = _build_module()
    problems = mod.selfcheck_records(train + ev)
    assert problems == [], problems[:20]


def test_split_is_by_item_and_disjoint(data):
    train, ev = data
    tr = {(r["meta"]["corpus"], r["meta"]["item"]) for r in train}
    ev_items = {(r["meta"]["corpus"], r["meta"]["item"]) for r in ev}
    assert tr and ev_items
    assert tr & ev_items == set()


def test_no_api_key_material(data):
    train, ev = data
    mod = _build_module()
    blob = "".join(json.dumps(r) for r in train + ev)
    assert mod.KEY_PAT.search(blob) is None


def test_no_excluded_grok_domains_source(data):
    train, ev = data
    for r in train + ev:
        m = r["meta"]
        assert not (m["corpus"] == "domains" and m["model"] == "grok")


def test_gold_consistent_with_ground_truth(data):
    """Spot the invariants the selfcheck enforces, independently of it."""
    train, ev = data
    for r in train + ev:
        m, gold = r["meta"], r["messages"][2]["content"]
        if m["klass"] in ("CITED_DENIED", "WHICH_CITED"):
            assert m["truth"] == "DENIED" and m["witness"] == "present"
        if m["klass"] in ("CONFIRMED_APPROVED", "WHICH_NONE_NO_FAILURE"):
            assert m["truth"] == "APPROVED" and m["witness"] == "present"
        if m["klass"] in ("CONS_MISSING", "WHICH_NONE_MISSING_DATA"):
            assert m["witness"] == "absent" and "MISSING DATA" in gold
        # never leak ground truth into the prompt
        assert m["truth"].lower() not in ("approved denied",)


def test_probes_match_deployed_protocol():
    """The reader input must reuse the canonical variant-0 probes verbatim."""
    lib = os.path.join(ROOT, "experiments", "lib", "dissociation.py")
    src = open(lib).read()
    mod = _build_module()
    assert mod.DECISION_PROBE.strip() in src
    assert mod.WHICH_PROBE.strip() in src


def test_chat_format(data):
    train, ev = data
    for r in train + ev:
        roles = [msg["role"] for msg in r["messages"]]
        assert roles == ["system", "user", "assistant"]
        assert all(msg["content"] for msg in r["messages"])
