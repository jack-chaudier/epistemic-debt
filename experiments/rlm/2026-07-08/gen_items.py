#!/usr/bin/env python3
"""R1 — Δ-audit of vanilla RLM: long-context item generator (see prereg_rlm_audit.md).

Each item is a (context, query) pair where the context is a COLLECTION of documents held
OUTSIDE the root model's window as addressable slices, and EXACTLY ONE slice is query-relevant.
The query = the standard policy + decision/WHICH probe for that one relevant document.

Two arms, reusing the existing confound-guarded corpora unchanged so the dissociation scorers
apply as-is:
  - "ledger":  slices drawn from experiments/lib/domains.py (6 synthetic policy domains). One
               relevant doc + (n_slices-1) distractor docs from OTHER operations (distinct codes,
               mixed domains). Ground truth exact.
  - "realdoc": slices drawn from experiments/realdoc/2026-07-08 (real NTSB accident prose with
               injected readings). One relevant airworthiness file + distractors from OTHER
               sources (distinct N-numbers). Real linguistic texture.

Addressability: the root sees only a MANIFEST — per slice, its id + header (doc type + code +
first words), never the readings. The relevant slice is identified by the code named in the
policy (candidate disclosure carries over: policy_text lists the 3 params). The root must issue a
sub-query to actually read a slice; the sub-call *return* (not the slice) re-enters its window.

Item schema:
  id, arm, truth (APPROVED|DENIED), failing_param, fail_slot, code, policy_text,
  parameters[{name,unit,value,policy,[dir,thr,passes]}], relevant_slice (index),
  slices[{slice_id, code, header, document}], n_slices

Confound guards (mechanical, in selfcheck):
  - value-collision: inherited from the source generators (each policy value uniquely retained()
    within its own relevant document — the witness-survival string check cannot false-match).
  - relevant-slice integrity: exactly one slice whose code == the item code; policy_text names it.
  - distinct codes within a context (the root can address the relevant slice unambiguously).
  - manifest headers carry NO policy reading (only doc type + code + prose lead-in).
  - verdict balance, one failing criterion when DENIED.

Stdlib only, seeded. Usage: python3 gen_items.py  ->  items.jsonl + selfcheck report.
"""
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "lib")
REALDOC = os.path.join(HERE, "..", "..", "realdoc", "2026-07-08")
sys.path.insert(0, LIB)
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
import domains                                    # noqa: E402
from runner3 import retained, match_param, numbers  # noqa: E402

SEED = 20260708
LEDGER_TARGETS = 24
LEDGER_SLICES = 20
REALDOC_TARGETS = 16
REALDOC_SLICES = 12
HEADER_WORDS = 22   # manifest header = first HEADER_WORDS words of the doc's cover paragraph


def _header(document):
    """First paragraph (cover story: doc type + code, no readings), truncated to HEADER_WORDS."""
    cover = document.split("\n\n", 1)[0]
    words = cover.split()
    h = " ".join(words[:HEADER_WORDS])
    if len(words) > HEADER_WORDS:
        h += " …"
    return h


def _build_context(target, distractors, n_slices, rng):
    """Assemble one context: target + distractors with distinct codes, target at a random slot."""
    chosen, seen_codes = [], {target["code"]}
    for d in distractors:
        if len(chosen) >= n_slices - 1:
            break
        if d["code"] in seen_codes:
            continue
        seen_codes.add(d["code"])
        chosen.append(d)
    if len(chosen) < n_slices - 1:
        raise RuntimeError("not enough distinct-code distractors")
    docs = chosen + [target]
    rng.shuffle(docs)
    relevant = docs.index(target)
    slices = [dict(slice_id=i, code=d["code"], header=_header(d["document"]),
                   document=d["document"]) for i, d in enumerate(docs)]
    return slices, relevant


def _pool_ledger(seed):
    """Generate a mixed-domain pool of confound-guarded documents (targets + distractors)."""
    pool = []
    for j, dk in enumerate(domains.DOMAIN_KEYS):
        pool += domains.gen_items(dk, seed + 991 * (j + 1), n=16)
    return pool


def _pool_realdoc():
    path = os.path.join(REALDOC, "items.jsonl")
    if not os.path.exists(path):
        raise RuntimeError("realdoc items.jsonl missing — run its gen_items.py first")
    return [json.loads(l) for l in open(path) if l.strip()]


def gen_items(seed=SEED):
    rng = random.Random(seed)
    items = []

    # ── ledger arm ────────────────────────────────────────────────────────────
    lpool = _pool_ledger(seed)
    approved = [it for it in lpool if it["truth"] == "APPROVED"]
    denied = [it for it in lpool if it["truth"] == "DENIED"]
    rng.shuffle(approved)
    rng.shuffle(denied)
    half = LEDGER_TARGETS // 2
    targets = approved[:half] + denied[:half]
    used_ids = {t["id"] for t in targets}
    rng.shuffle(targets)
    for i, target in enumerate(targets):
        drng = random.Random((seed * 100003) ^ (i + 1))
        distractors = [it for it in lpool if it["id"] not in used_ids]
        drng.shuffle(distractors)
        slices, relevant = _build_context(target, distractors, LEDGER_SLICES, drng)
        items.append(_pack("ledger", i, target, slices, relevant))

    # ── realdoc arm ───────────────────────────────────────────────────────────
    rpool = _pool_realdoc()
    r_app = [it for it in rpool if it["truth"] == "APPROVED"]
    r_den = [it for it in rpool if it["truth"] == "DENIED"]
    rng.shuffle(r_app)
    rng.shuffle(r_den)
    rhalf = REALDOC_TARGETS // 2
    r_targets = r_app[:rhalf] + r_den[:rhalf]
    rng.shuffle(r_targets)
    for i, target in enumerate(r_targets):
        drng = random.Random((seed * 100019) ^ (i + 1))
        # distractors: other items from OTHER source narratives (distinct accident + code)
        tgt_src = target["source_id"]
        distractors = [it for it in rpool if it["source_id"] != tgt_src]
        drng.shuffle(distractors)
        slices, relevant = _build_context(target, distractors, REALDOC_SLICES, drng)
        items.append(_pack("realdoc", i, target, slices, relevant))

    return items


def _pack(arm, i, target, slices, relevant):
    return dict(
        id=f"{arm}-{i:03d}", arm=arm, truth=target["truth"],
        failing_param=target["failing_param"], fail_slot=target["fail_slot"],
        code=target["code"], policy_text=target["policy_text"],
        parameters=target["parameters"], relevant_slice=relevant,
        n_slices=len(slices), slices=slices)


def selfcheck(items):
    problems = []
    n_app = {"ledger": 0, "realdoc": 0}
    n_tot = {"ledger": 0, "realdoc": 0}
    for it in items:
        n_tot[it["arm"]] += 1
        if it["truth"] == "APPROVED":
            n_app[it["arm"]] += 1
        # exactly one slice matches the item code, and it is relevant_slice
        matches = [s for s in it["slices"] if s["code"] == it["code"]]
        if len(matches) != 1:
            problems.append((it["id"], "code-not-unique", it["code"], len(matches)))
        elif it["slices"][it["relevant_slice"]]["code"] != it["code"]:
            problems.append((it["id"], "relevant-slice-mismatch", it["code"]))
        # distinct codes across the context
        codes = [s["code"] for s in it["slices"]]
        if len(set(codes)) != len(codes):
            problems.append((it["id"], "duplicate-slice-code"))
        # policy names the code (addressability) and the 3 candidate params (disclosure).
        # NB: ledger items carry all 12 readings; only the 3 policy params are disclosed/checked.
        pol = [p for p in it["parameters"] if p.get("policy")]
        if it["code"] not in it["policy_text"]:
            problems.append((it["id"], "code-not-in-policy", it["code"]))
        for p in pol:
            if p["name"] not in it["policy_text"]:
                problems.append((it["id"], "param-not-disclosed", p["name"]))
        # policy value uniquely retained within the RELEVANT document (witness-survival check
        # cannot false-match a sibling policy reading in that doc)
        rel_doc = it["slices"][it["relevant_slice"]]["document"]
        rel_nums = numbers(rel_doc)
        vals = [p["value"] for p in it["parameters"]]
        for p in pol:
            hits = sum(1 for v in vals if retained(f"{v}", p["value"]))
            if hits != 1:
                problems.append((it["id"], "value-collision-in-relevant", p["name"], hits))
        # manifest headers carry no policy reading of the relevant doc
        for s in it["slices"]:
            if s["code"] != it["code"]:
                continue
            for x in numbers(s["header"]):
                if any(retained(f"{x}", p["value"]) for p in pol):
                    problems.append((it["id"], "header-leaks-reading", s["slice_id"]))
        # failing param maps back to itself
        if it["failing_param"] and match_param(it["failing_param"], it["parameters"]) != it["failing_param"]:
            problems.append((it["id"], "param-unmatch", it["failing_param"]))
        fails = [p for p in pol if not p.get("passes", True)]
        if it["truth"] == "DENIED" and len(fails) != 1:
            problems.append((it["id"], "denied-not-one-fail", len(fails)))
        if it["truth"] == "APPROVED" and fails:
            problems.append((it["id"], "approved-has-fail", len(fails)))
    for arm in n_tot:
        if n_tot[arm] and n_app[arm] * 2 != n_tot[arm]:
            problems.append((arm, "verdict-imbalance", n_app[arm], n_tot[arm]))
    return problems


def main():
    items = gen_items()
    probs = selfcheck(items)
    with open(os.path.join(HERE, "items.jsonl"), "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    by_arm = {}
    for it in items:
        by_arm.setdefault(it["arm"], []).append(it)
    print(f"items: {len(items)}")
    for arm, sub in by_arm.items():
        n_app = sum(1 for it in sub if it["truth"] == "APPROVED")
        ns = sub[0]["n_slices"]
        ctx_words = [sum(len(s["document"].split()) for s in it["slices"]) for it in sub]
        print(f"  {arm}: {len(sub)} items ({n_app} A / {len(sub)-n_app} D), {ns} slices/ctx, "
              f"ctx words med {sorted(ctx_words)[len(ctx_words)//2]}")
    print(f"selfcheck problems: {len(probs)}")
    for p in probs[:40]:
        print("  ", p)


if __name__ == "__main__":
    main()
