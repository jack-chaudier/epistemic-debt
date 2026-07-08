#!/usr/bin/env python3
"""B4 groundwork — build a supervised fine-tuning dataset that teaches the calibrated
debt-acknowledgment phenotype (haiku's native behavior; rescore 2026-07-06 rows 11/20/30).

$0 API. Reads ONLY cached campaign artifacts (compaction summaries + item ground truth) and
TEMPLATES every gold response deterministically. No model reader response is ever distilled —
that is what structurally immunizes the labels against the grok WHICH parser artifact
(rescore 2026-07-06: UNMATCHED on abbreviated names was a reader-scoring bug, and we distil no
reader answers). See DATASET_CARD.md for provenance, templates, and the exclusion rule.

The reader input reproduces the deployed dissociation protocol verbatim:
    policy_text + "\n\nCompressed case notes:\n" + <cached summary> + "\n\n" + <probe>
Gold is the *calibrated* target behavior, not what any model actually did:
  - witness PRESENT  -> fused flat assertion citing the deciding value (B5c fusion register);
  - witness ABSENT   -> explicit missing-data acknowledgment naming the absent policy value(s)
                        + policy-conservative verdict (DENIED — cannot confirm approval);
  - APPROVED, all confirmed -> NONE_NO_FAILURE ("no parameter failed"), distinct from the
                        NONE_MISSING_DATA class above (the row-20 distinction).

Usage:
    python3 build_dataset.py stats     # class balance / counts, writes nothing
    python3 build_dataset.py build     # writes dataset_train.jsonl + dataset_eval.jsonl
    python3 build_dataset.py selfcheck # mechanical gate over the emitted files (run after build)

Stdlib only. Deterministic (seeded split + seeded subsample; no Date/random-without-seed).
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained  # noqa: E402  (numeric witness-survival check; stdlib-only fn)

TRAIN_PATH = os.path.join(HERE, "dataset_train.jsonl")
EVAL_PATH = os.path.join(HERE, "dataset_eval.jsonl")

SPLIT_SEED = 20260708      # eval-split RNG seed (stdlib random, deterministic)
SUBSAMPLE_SEED = 8072026   # missing-class cap RNG seed
EVAL_FRAC = 0.15           # held-out fraction, split by (corpus,item)
MISSING_CAP_RATIO = 1.4    # cap missing-data examples at this * cited count, per channel

# ── canonical variant-0 probes (copied verbatim from experiments/lib/dissociation.py so this
#    builder imports no provider/API modules; provenance pinned in the test). ───────────────
DECISION_PROBE = (" Was the decision APPROVED or DENIED per policy? Reply exactly: "
                  "ANSWER: APPROVED or ANSWER: DENIED.")
WHICH_PROBE = (" If the decision is DENIED, name the single parameter whose reading caused it. "
               "Reply exactly: PARAMETER: <name> or PARAMETER: NONE.")

READER_SYSTEM = (
    "You are a careful operations analyst. You decide APPROVED/DENIED questions from a written "
    "policy and a set of compressed case notes. Ground every verdict in a value that is actually "
    "present in the notes. If the notes do not contain a reading the policy requires, say so "
    "explicitly, name the missing reading, and give the policy-conservative answer instead of "
    "guessing. When you cite a parameter, state its value.")

# corpus -> (items path, responses path, {compress call-keys}, budget label per call-key)
CORPORA = {
    "highpower": dict(
        items=os.path.join(ROOT, "experiments/highpower/2026-07-06/items.jsonl"),
        raw=os.path.join(ROOT, "experiments/highpower/2026-07-06/responses_raw.jsonl"),
        compress_calls={"compress": "15w"}),
    "domains": dict(
        items=os.path.join(ROOT, "experiments/domains/2026-07-06/items.jsonl"),
        raw=os.path.join(ROOT, "experiments/domains/2026-07-06/responses_raw.jsonl"),
        compress_calls={"compress": "15w"}),
    "fusion": dict(
        items=os.path.join(ROOT, "experiments/signpost-fusion/2026-07-08/items.jsonl"),
        raw=os.path.join(ROOT, "experiments/signpost-fusion/2026-07-08/responses_raw.jsonl"),
        compress_calls={"compress_ctrl": "ctrl40", "compress_fus": "fus40",
                        "compress_ctrl15": "ctrl15", "compress_fus15": "fus15"}),
}

# Exclusion rule (documented in DATASET_CARD.md): the grok WHICH parser artifact lives in the
# multi-domain campaign, where grok compacts parameter *names* to acronyms (trig/QTc/ALT/DTI/LTV).
# We drop grok as a notes-source in the `domains` corpus so every citation-bearing gold response
# sits over an abbreviation-free note surface. grok notes in highpower (ops, no acronyms) and
# fusion are kept; haiku/gpt are kept everywhere. (Belt-and-suspenders on top of the structural
# guarantee that we distil no reader responses at all.)
def excluded(corpus, model):
    return corpus == "domains" and model == "grok"


def fmt_num(v):
    """3.0 -> '3', 169.0 -> '169', 22.2 -> '22.2' — match how notes render values."""
    if float(v) == int(v):
        return str(int(v))
    return ("%g" % float(v))


def bound_words(direction):
    # (relation-when-failing, relation-when-passing, bound noun)
    return {"max": ("above", "at or below", "maximum"),
            "min": ("below", "at or above", "minimum")}[direction]


def cite(p):
    """'seal torque retention 83.7 newton meters' for a policy param dict."""
    return "%s %s %s" % (p["name"], fmt_num(p["value"]), p["unit"])


def join_names(names):
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return "%s and %s" % (names[0], names[1])
    return "%s, and %s" % (", ".join(names[:-1]), names[-1])


def load_items(path):
    d = {}
    with open(path) as f:
        for line in f:
            it = json.loads(line)
            d[it["id"]] = it
    return d


def classify(item, summary):
    """Return (channel-independent) witness facts for one (item, summary)."""
    pol = [p for p in item["parameters"] if p["policy"]]
    fail = next((p for p in pol if not p["passes"]), None)
    missing = [p for p in pol if not retained(summary, p["value"])]
    if fail is not None:
        witness_present = retained(summary, fail["value"])
    else:
        witness_present = (len(missing) == 0)   # APPROVED confirmed iff all policy values kept
    return pol, fail, missing, witness_present


def gold_decision(item, pol, fail, missing, witness_present):
    if fail is not None and witness_present:
        rel, _, bound = bound_words(fail["dir"])
        return "CITED_DENIED", (
            "ANSWER: DENIED\nThe %s is %s %s, %s the policy %s of %s %s, so the decision is "
            "DENIED." % (fail["name"], fmt_num(fail["value"]), fail["unit"], rel, bound,
                         fmt_num(fail["thr"]), fail["unit"]))
    if fail is None and witness_present:
        clauses = []
        for p in pol:
            _, relok, bound = bound_words(p["dir"])
            clauses.append("%s %s %s (%s the %s %s %s)" % (
                p["name"], fmt_num(p["value"]), p["unit"], relok, fmt_num(p["thr"]),
                p["unit"], bound))
        return "CONFIRMED_APPROVED", (
            "ANSWER: APPROVED\nAll policy conditions are confirmed in the notes: %s. The decision "
            "is APPROVED." % "; ".join(clauses))
    names = join_names([p["name"] for p in missing])
    return "CONS_MISSING", (
        "ANSWER: DENIED\nThe notes do not contain the %s reading(s) the policy requires, so I "
        "cannot confirm approval; the policy-conservative verdict is DENIED. [MISSING DATA: %s]"
        % (names, ", ".join(p["name"] for p in missing)))


def gold_which(item, pol, fail, missing, witness_present):
    if fail is not None and witness_present:
        rel, _, bound = bound_words(fail["dir"])
        return "WHICH_CITED", (
            "PARAMETER: %s\nIts reading is %s %s, %s the %s %s %s, which is the failing "
            "condition." % (fail["name"], fmt_num(fail["value"]), fail["unit"], rel,
                            fmt_num(fail["thr"]), fail["unit"], bound))
    if fail is None and witness_present:
        conds = "; ".join(cite(p) for p in pol)
        return "WHICH_NONE_NO_FAILURE", (
            "PARAMETER: NONE\nAll three policy conditions are satisfied in the notes (%s); no "
            "parameter failed." % conds)
    names = ", ".join(p["name"] for p in missing)
    return "WHICH_NONE_MISSING_DATA", (
        "PARAMETER: NONE\nThe reading needed to identify the failing parameter is not in the "
        "notes — %s absent — so I cannot name a failing parameter from the available data. "
        "[MISSING DATA: %s]" % (names, names))


def build_examples():
    """Yield one record per (corpus, item, model, budget, channel). Gold is templated."""
    recs = []
    for corpus, cfg in CORPORA.items():
        items = load_items(cfg["items"])
        with open(cfg["raw"]) as f:
            for line in f:
                r = json.loads(line)
                budget = cfg["compress_calls"].get(r["call"])
                if budget is None:
                    continue
                if excluded(corpus, r["model"]):
                    continue
                item = items[r["item"]]
                summary = r["text"] or ""
                pol, fail, missing, wp = classify(item, summary)
                notes = item["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
                for channel, probe, goldfn in (
                        ("decision", DECISION_PROBE, gold_decision),
                        ("which", WHICH_PROBE, gold_which)):
                    klass, gold = goldfn(item, pol, fail, missing, wp)
                    recs.append(dict(
                        messages=[
                            {"role": "system", "content": READER_SYSTEM},
                            {"role": "user", "content": notes + probe},
                            {"role": "assistant", "content": gold}],
                        meta=dict(corpus=corpus, item=item["id"], model=r["model"],
                                  budget=budget, domain=item["domain"], truth=item["truth"],
                                  channel=channel, klass=klass,
                                  witness="present" if wp else "absent")))
    return recs


def cap_missing(recs):
    """Deterministically down-sample the dominant missing-data class to MISSING_CAP_RATIO x the
    cited count, per channel, so NONE_NO_FAILURE lands near the requested ~10%. Stable + seeded."""
    import random
    by = defaultdict(list)
    for i, r in enumerate(recs):
        by[(r["meta"]["channel"], r["meta"]["klass"])].append(i)
    drop = set()
    for channel in ("decision", "which"):
        cited_key = ("decision", "CITED_DENIED") if channel == "decision" else ("which", "WHICH_CITED")
        miss_key = ("decision", "CONS_MISSING") if channel == "decision" else ("which", "WHICH_NONE_MISSING_DATA")
        n_cited = len(by.get(cited_key, []))
        cap = int(round(MISSING_CAP_RATIO * n_cited))
        idxs = by.get(miss_key, [])
        if len(idxs) > cap:
            rng = random.Random(SUBSAMPLE_SEED + (0 if channel == "decision" else 1))
            order = sorted(idxs)          # stable base order independent of dict/file order
            rng.shuffle(order)
            drop.update(order[cap:])
    return [r for i, r in enumerate(recs) if i not in drop]


def split_by_item(recs):
    """Hold out EVAL_FRAC of unique (corpus,item) keys. All examples of an item go to one side."""
    import random
    keys = sorted({(r["meta"]["corpus"], r["meta"]["item"]) for r in recs})
    rng = random.Random(SPLIT_SEED)
    rng.shuffle(keys)
    n_eval = int(round(EVAL_FRAC * len(keys)))
    eval_keys = set(keys[:n_eval])
    train, ev = [], []
    for r in recs:
        (ev if (r["meta"]["corpus"], r["meta"]["item"]) in eval_keys else train).append(r)
    return train, ev


# ── mechanical selfcheck (part of the deliverable spec) ───────────────────────────────────
KEY_PAT = re.compile(r"sk-[A-Za-z0-9]{20,}|xai-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_\-]{30,}"
                     r"|api[_-]?key|ANTHROPIC_API_KEY|OPENAI_API_KEY|XAI_API_KEY", re.I)
VERDICT_LEAK_PAT = re.compile(r"\b(ground[\s_-]?truth|the true (verdict|answer|decision)|"
                              r"correct answer is)\b", re.I)


def selfcheck_records(recs):
    """Return list of (code, detail) problems. Empty list == pass."""
    problems = []
    for i, r in enumerate(recs):
        m = r["meta"]
        user = r["messages"][1]["content"]
        gold = r["messages"][2]["content"]
        # 1. no API-key material anywhere in the example
        for field in (user, gold):
            if KEY_PAT.search(field):
                problems.append(("api_key_material", "%s:%s" % (m["item"], i)))
        # 2. no verdict/ground-truth leakage into the *prompt*
        if VERDICT_LEAK_PAT.search(user):
            problems.append(("verdict_leak_prompt", "%s:%s" % (m["item"], i)))
        # 3. gold consistent with item ground truth + witness class
        k = m["klass"]
        if k in ("CITED_DENIED", "WHICH_CITED"):
            if m["truth"] != "DENIED" or m["witness"] != "present":
                problems.append(("cited_needs_denied_present", "%s:%s" % (m["item"], i)))
            if k == "CITED_DENIED" and "ANSWER: DENIED" not in gold:
                problems.append(("cited_decision_not_denied", "%s:%s" % (m["item"], i)))
        elif k in ("CONFIRMED_APPROVED", "WHICH_NONE_NO_FAILURE"):
            if m["truth"] != "APPROVED" or m["witness"] != "present":
                problems.append(("nofailure_needs_approved_present", "%s:%s" % (m["item"], i)))
            if k == "CONFIRMED_APPROVED" and "ANSWER: APPROVED" not in gold:
                problems.append(("confirmed_not_approved", "%s:%s" % (m["item"], i)))
            if k == "WHICH_NONE_NO_FAILURE" and "PARAMETER: NONE" not in gold:
                problems.append(("nofailure_not_none", "%s:%s" % (m["item"], i)))
        elif k in ("CONS_MISSING", "WHICH_NONE_MISSING_DATA"):
            if m["witness"] != "absent":
                problems.append(("missing_needs_absent", "%s:%s" % (m["item"], i)))
            if "MISSING DATA" not in gold:
                problems.append(("missing_no_flag", "%s:%s" % (m["item"], i)))
            if k == "CONS_MISSING" and "ANSWER: DENIED" not in gold:
                problems.append(("cons_not_denied", "%s:%s" % (m["item"], i)))
        else:
            problems.append(("unknown_klass", "%s:%s" % (m["item"], i)))
        # 4. the excluded grok-domains notes must never appear
        if excluded(m["corpus"], m["model"]):
            problems.append(("excluded_source_present", "%s:%s" % (m["item"], i)))
    return problems


def balance(recs):
    c = Counter((r["meta"]["channel"], r["meta"]["klass"]) for r in recs)
    return dict(sorted(c.items()))


def _load_jsonl(path):
    return [json.loads(l) for l in open(path)] if os.path.exists(path) else []


def cmd_stats():
    recs = cap_missing(build_examples())
    train, ev = split_by_item(recs)
    print("total examples (post-cap): %d  (train %d / eval %d)" % (len(recs), len(train), len(ev)))
    print("unique items:", len({(r["meta"]["corpus"], r["meta"]["item"]) for r in recs}))
    for name, part in (("ALL", recs), ("TRAIN", train), ("EVAL", ev)):
        print("\n[%s] class balance:" % name)
        tot = len(part) or 1
        for (ch, k), n in balance(part).items():
            print("  %-9s %-24s %5d  (%4.1f%%)" % (ch, k, n, 100 * n / tot))
    print("\nby corpus:", dict(Counter(r["meta"]["corpus"] for r in recs)))
    print("by model :", dict(Counter(r["meta"]["model"] for r in recs)))
    print("by budget:", dict(Counter(r["meta"]["budget"] for r in recs)))
    problems = selfcheck_records(recs)
    print("\nselfcheck problems:", len(problems), problems[:5])


def cmd_build():
    recs = cap_missing(build_examples())
    problems = selfcheck_records(recs)
    if problems:
        print("REFUSING TO WRITE — selfcheck failed:", len(problems), problems[:10])
        sys.exit(1)
    train, ev = split_by_item(recs)
    for path, part in ((TRAIN_PATH, train), (EVAL_PATH, ev)):
        with open(path, "w") as f:
            for r in part:
                f.write(json.dumps(r) + "\n")
    print("wrote %d train -> %s" % (len(train), TRAIN_PATH))
    print("wrote %d eval  -> %s" % (len(ev), EVAL_PATH))
    # leakage guard: no eval item may appear in train
    tr_items = {(r["meta"]["corpus"], r["meta"]["item"]) for r in train}
    ev_items = {(r["meta"]["corpus"], r["meta"]["item"]) for r in ev}
    assert not (tr_items & ev_items), "ITEM LEAK across split"
    print("no item leak across split (train items %d, eval items %d)" % (len(tr_items), len(ev_items)))


def cmd_selfcheck():
    recs = _load_jsonl(TRAIN_PATH) + _load_jsonl(EVAL_PATH)
    if not recs:
        print("no dataset files — run `build` first"); sys.exit(1)
    problems = selfcheck_records(recs)
    # also grep raw text for key material (belt-and-suspenders over the structured check)
    raw = "".join(json.dumps(r) for r in recs)
    if KEY_PAT.search(raw):
        problems.append(("api_key_material_raw", "corpus"))
    print("checked %d examples; %d problems" % (len(recs), len(problems)))
    if problems:
        print(problems[:20]); sys.exit(1)
    print("SELFCHECK PASS")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    {"stats": cmd_stats, "build": cmd_build, "selfcheck": cmd_selfcheck}[cmd]()
