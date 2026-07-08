#!/usr/bin/env python3
"""Item generator for the reader-inference-boundary experiment. See prereg.

Four derivability classes over a 3-condition conjunctive policy, ground truth DENIED with
exactly ONE failing policy parameter (the culprit). No compressor: the "case notes" are
constructed deterministically so the required read-channel operation is controlled exactly.

  (a) UNDERIVABLE : notes contain none of the 3 policy readings (distractors only).
  (b) ELIM        : the 2 non-culprit readings present plainly (both pass); culprit omitted.
  (c) ARITHMETIC  : 1 non-culprit plain (pass); culprit + other non-culprit each given only as
                    a one-step arithmetic expression (base +/- offset). Culprit resolves to a
                    fail, the paired one to a pass. Nothing absent; both arithmetic candidates
                    are surface-symmetric so ONLY computation isolates the culprit.
  (d) RETRIEVAL   : all 3 plain; culprit fails, others pass (positive control).

Numeric values are synthetic integers anchored to each domain's band midpoint (register and
vocabulary come from domains.py; exact calibration is irrelevant to a read-channel probe).
Stdlib only, seeded. `gen_items()` -> list; `selfcheck(items)` -> [] iff clean.
"""
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D  # noqa: E402  (DOMAINS, CODES, LEADS, collides, retained, match_param, VERDICT_WORDS, cond_clause)
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v2"))
from runner2 import cond_clause  # noqa: E402

CLASSES = ("a", "b", "c", "d")
N_PER_CLASS = 60                       # 60 x 4 = 240 items
CLASS_SEED = {"a": 780801, "b": 780802, "c": 780803, "d": 780804}

PLAIN_T = [
    "The {name} was recorded at {v} {u}.",
    "The {name} reading came back at {v} {u}.",
    "Logged {name}: {v} {u}.",
    "The {name} stood at {v} {u} in the file.",
]
ARITH_T = [
    "The {name} came in {o} {u} {dw} the earlier baseline of {base} {u}.",
    "The {name} was {o} {u} {dw} a prior reading of {base} {u}.",
    "Relative to a {base} {u} baseline, the {name} moved {o} {u} {dw}.",
]
FILLER = [
    "No other entries in the record required follow-up.",
    "The remaining lines were routine administrative notes.",
    "Standard handover notes were attached without further detail.",
    "Other observations in the file were procedural only.",
    "The rest of the record repeated earlier logistics remarks.",
]


def _eligible_params(spec):
    # integer-friendly bands: wide enough to place a threshold with pass/fail margins + offsets
    return [p for p in spec["params"] if (p[4] - p[3]) >= 16 and p[4] >= 24]


def _margin(t):
    return max(3, round(0.22 * abs(t)))


def _fail_value(t, direction, m):
    return t + m if direction == "max" else t - m


def _pass_value(t, direction, m):
    return t - m if direction == "max" else t + m


def _dodge(value, thr, forbidden):
    """Move `value` off any collision, always AWAY from the threshold so the pass/fail
    margin can only grow, never shrink below the designed 22%."""
    step = 1 if value > thr else -1
    while D.collides(value, forbidden):
        value += step
    return value


def _arith_encode(rng, value, forbidden):
    """Encode integer `value` as (base, offset, dirword) with base +/- offset == value.
    dirword and offset drawn independently of pass/fail so no surface feature leaks the role.
    Returns (base, offset, dirword) or None if no clean encoding exists."""
    order = [(o, dw) for o in range(3, 23) for dw in ("above", "below")]
    rng.shuffle(order)
    for o, dw in order:
        base = value - o if dw == "above" else value + o
        if base <= 0 or o == base:
            continue
        if D.collides(base, forbidden) or D.collides(o, forbidden):
            continue
        return base, o, dw
    return None


def _try_build(cls, i, dom_key, spec, drng):
    """Build one item; return dict or None if this seed can't produce a clean encoding."""
    elig = _eligible_params(spec)
    chosen = drng.sample(elig, 3)                 # the 3 disclosed policy candidates
    culprit_slot = drng.randrange(3)
    forbidden = set()
    pol = []
    for k, (name, unit, direction, lo, hi, dec) in enumerate(chosen):
        t = int(round(drng.uniform(lo + 0.30 * (hi - lo), hi - 0.30 * (hi - lo))))
        t = _dodge(t, t + 1, forbidden)           # keep thresholds distinct
        forbidden.add(float(t))
        m = _margin(t)
        passes = (k != culprit_slot)
        value = _pass_value(t, direction, m) if passes else _fail_value(t, direction, m)
        value = _dodge(value, t, forbidden)       # dodge collisions AWAY from threshold
        forbidden.add(float(value))
        pol.append(dict(name=name, unit=unit, dir=direction, thr=t, value=value,
                        passes=passes, dec=0))
    culprit = pol[culprit_slot]["name"]

    others = [k for k in range(3) if k != culprit_slot]
    drng.shuffle(others)
    enc = {}
    if cls == "a":
        for k in range(3):
            enc[k] = "absent"
    elif cls == "b":
        enc[culprit_slot] = "absent"
        enc[others[0]] = "plain"
        enc[others[1]] = "plain"
    elif cls == "c":
        enc[others[0]] = "plain"          # 1 non-culprit plain (passes)
        enc[culprit_slot] = "arith"       # culprit as arithmetic (fails)
        enc[others[1]] = "arith"          # other non-culprit as arithmetic (passes)
    elif cls == "d":
        for k in range(3):
            enc[k] = "plain"

    note_lines = []
    arith_meta = {}
    for k in range(3):
        p = pol[k]
        if enc[k] == "plain":
            note_lines.append(drng.choice(PLAIN_T).format(name=p["name"], v=p["value"], u=p["unit"]))
        elif enc[k] == "arith":
            res = _arith_encode(drng, p["value"], forbidden | {float(p["value"])})
            if res is None:
                return None
            base, o, dw = res
            forbidden.add(float(base))
            forbidden.add(float(o))
            note_lines.append(drng.choice(ARITH_T).format(name=p["name"], o=o, u=p["unit"],
                                                          dw=dw, base=base))
            arith_meta[k] = dict(base=base, offset=o, dirword=dw)
        # absent: no line

    n_fill = 2 if cls in ("a", "d") else 1
    fills = drng.sample(FILLER, n_fill)
    note_lines = note_lines + fills
    drng.shuffle(note_lines)
    notes = "\n".join(f"- {ln}" for ln in note_lines)

    p0, p1, p2 = pol
    policy_text = (f"POLICY: {spec['label'].capitalize()} case {i:03d} is APPROVED only if "
                   f"{cond_clause(p0['name'], p0['unit'], p0['dir'], p0['thr'])} AND "
                   f"{cond_clause(p1['name'], p1['unit'], p1['dir'], p1['thr'])} AND "
                   f"{cond_clause(p2['name'], p2['unit'], p2['dir'], p2['thr'])}; "
                   f"otherwise it is DENIED.")

    # DIRECT-ARITH capacity control (class c only): balanced across items —
    # even i -> ask the culprit expression (truth FAIL); odd i -> paired passer (truth PASS)
    arith_probe = None
    if cls == "c":
        if i % 2 == 0:
            k, truth = culprit_slot, "FAIL"
        else:
            k, truth = others[1], "PASS"
        meta = arith_meta.get(k)
        if meta is None:
            return None
        p = pol[k]
        arith_probe = dict(name=p["name"], unit=p["unit"], dir=p["dir"], thr=p["thr"],
                           base=meta["base"], offset=meta["offset"], dirword=meta["dirword"],
                           truth=truth)

    return dict(
        id=f"rib-{cls}-{i:03d}", cls=cls, domain=dom_key, truth="DENIED", culprit=culprit,
        culprit_slot=culprit_slot, policy_text=policy_text, notes=notes,
        parameters=[dict(name=p["name"], unit=p["unit"], value=p["value"], policy=True,
                         dir=p["dir"], thr=p["thr"], passes=p["passes"]) for p in pol],
        arith=arith_meta, arith_probe=arith_probe)


def gen_class(cls, seed):
    items = []
    n_dom = len(D.DOMAIN_KEYS)
    for i in range(N_PER_CLASS):
        dom_key = D.DOMAIN_KEYS[i % n_dom]
        spec = D.DOMAINS[dom_key]
        for attempt in range(200):
            drng = random.Random((seed * 100003) ^ (i + 1) ^ (attempt * 0x9e3779b1))
            it = _try_build(cls, i, dom_key, spec, drng)
            if it is not None:
                items.append(it)
                break
        else:
            raise RuntimeError(f"{cls} item {i}: no clean encoding after 200 attempts")
    return items


def gen_items():
    items = []
    for cls in CLASSES:
        items.extend(gen_class(cls, CLASS_SEED[cls]))
    return items


NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _nums(text):
    return [float(x) for x in NUM_RE.findall(text.replace(",", ""))]


def selfcheck(items):
    """Mechanically guard every generation confound before any spend. Returns list of problems."""
    problems = []
    by_class = {c: [] for c in CLASSES}
    for it in items:
        by_class[it["cls"]].append(it)
        pol = it["parameters"]
        cs = it["culprit_slot"]
        # exactly one failing policy param, and it is the culprit
        failing = [k for k, p in enumerate(pol) if not p["passes"]]
        if failing != [cs]:
            problems.append((it["id"], "not-single-culprit", failing))
        if pol[cs]["name"] != it["culprit"]:
            problems.append((it["id"], "culprit-mismatch"))
        # culprit truly fails its threshold; others truly pass; margins >= 15%
        for k, p in enumerate(pol):
            fails = (p["value"] > p["thr"]) if p["dir"] == "max" else (p["value"] < p["thr"])
            if fails == p["passes"]:
                problems.append((it["id"], "passfail-inconsistent", p["name"]))
            marg = abs(p["value"] - p["thr"]) / max(1, abs(p["thr"]))
            if marg < 0.15:
                problems.append((it["id"], "margin-too-small", p["name"], round(marg, 3)))
        # culprit maps to itself under the fuzzy parser (no acronym artifact)
        if D.match_param(it["culprit"], pol) != it["culprit"]:
            problems.append((it["id"], "culprit-unmatch", it["culprit"]))
        # verdict / threshold language must not leak into the notes
        if D.VERDICT_WORDS.search(it["notes"]):
            problems.append((it["id"], "verdict-leak", D.VERDICT_WORDS.search(it["notes"]).group(0)))
        # policy_text discloses all three candidate names (candidate-set disclosure = TRUE, stated)
        for p in pol:
            if p["name"] not in it["policy_text"]:
                problems.append((it["id"], "candidate-not-disclosed", p["name"]))

        note_nums = _nums(it["notes"])
        present = lambda v: any(abs(x - v) < 1e-9 or (v and abs(x - v) / abs(v) <= 0.01) for x in note_nums)
        cls = it["cls"]
        # per-class structural guarantees
        if cls == "a":
            for p in pol:
                if present(p["value"]):
                    problems.append((it["id"], "a-value-present", p["name"]))
        elif cls == "b":
            if present(pol[cs]["value"]):
                problems.append((it["id"], "b-culprit-value-present", it["culprit"]))
            for k, p in enumerate(pol):
                if k != cs and not present(p["value"]):
                    problems.append((it["id"], "b-noncauseval-absent", p["name"]))
        elif cls == "c":
            # exactly the two arithmetic params encoded (culprit + one non-culprit); their
            # resolved values NOT string-present, so only computation isolates the culprit
            arith_keys = {int(k) for k in it["arith"].keys()}
            if len(arith_keys) != 2 or cs not in arith_keys:
                problems.append((it["id"], "c-arith-structure", sorted(arith_keys)))
            for k, meta in it["arith"].items():
                k = int(k)
                resolved = meta["base"] + meta["offset"] if meta["dirword"] == "above" else meta["base"] - meta["offset"]
                if resolved != pol[k]["value"]:
                    problems.append((it["id"], "c-arith-wrong", pol[k]["name"], resolved, pol[k]["value"]))
                if present(pol[k]["value"]):
                    problems.append((it["id"], "c-resolved-present", pol[k]["name"]))
            # the one plain non-culprit value IS present
            plain_ks = [k for k in range(3) if k != cs and k not in arith_keys]
            for k in plain_ks:
                if not present(pol[k]["value"]):
                    problems.append((it["id"], "c-plain-absent", pol[k]["name"]))
        elif cls == "d":
            for p in pol:
                if not present(p["value"]):
                    problems.append((it["id"], "d-value-absent", p["name"]))

    # class sizes
    for c in CLASSES:
        if len(by_class[c]) != N_PER_CLASS:
            problems.append(("CORPUS", "class-size", c, len(by_class[c])))

    # (c) surface-balance guards: no first-order surface feature may reveal the culprit.
    c_items = by_class["c"]
    if c_items:
        n = len(c_items)
        culprit_above = 0     # culprit encoded with dirword "above"
        culprit_bigger_off = 0  # culprit offset > paired offset
        culprit_base_lower = 0  # culprit base < paired base
        culprit_base_below_t = 0  # culprit base < its own threshold
        for it in c_items:
            cs = it["culprit_slot"]
            am = {int(k): v for k, v in it["arith"].items()}
            others_arith = [k for k in am if k != cs]
            if cs not in am or not others_arith:
                continue
            cm = am[cs]
            om = am[others_arith[0]]
            culprit_above += int(cm["dirword"] == "above")
            culprit_bigger_off += int(cm["offset"] > om["offset"])
            culprit_base_lower += int(cm["base"] < om["base"])
            culprit_base_below_t += int(cm["base"] < it["parameters"][cs]["thr"])
        for label, k, tol in (("dirword-above", culprit_above, 0.15),
                              ("offset-bigger", culprit_bigger_off, 0.15),
                              ("base-lower", culprit_base_lower, 0.15),
                              ("base-below-thr", culprit_base_below_t, 0.20)):
            frac = k / n
            if abs(frac - 0.5) > tol:
                problems.append(("CORPUS-C", "surface-leak", label, round(frac, 3)))
    return problems


if __name__ == "__main__":
    import json
    items = gen_items()
    probs = selfcheck(items)
    out = os.path.join(HERE, "items.jsonl")
    if probs:
        print(f"SELFCHECK FAILED ({len(probs)} problems):")
        for p in probs[:40]:
            print("  ", p)
        sys.exit(1)
    with open(out, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    from collections import Counter
    print(f"generated {len(items)} items -> {out}")
    print("per class:", dict(Counter(it["cls"] for it in items)))
    print("per domain:", dict(Counter(it["domain"] for it in items)))
    print("selfcheck: CLEAN (0 problems)")
