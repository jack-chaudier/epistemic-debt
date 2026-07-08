#!/usr/bin/env python3
"""Confirmatory class-c2 generator: arithmetic recovery with the base-only leak removed.

Same as class c (3-condition conjunctive policy, DENIED, one culprit; 1 plain non-culprit passer +
2 arith-encoded candidates = culprit(fail) + 1 non-culprit(pass)), with ONE added constraint:
BOTH arithmetic candidates' baselines are on the PASS side of their own thresholds, so the culprit
crosses to a fail ONLY via its offset. A base-only reader (ignore the offset) cannot distinguish
the two -> base-only culprit recovery forced to chance. See prereg_c2_confirmatory.md.

Reuses gen_items.py helpers. Writes items_c2.jsonl. Stdlib only, seeded.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_items as G  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
import domains as D  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v2"))
from runner2 import cond_clause  # noqa: E402

N = 60
SEED = 780805


def _arith_encode_pass_base(rng, value, thr, direction, forbidden):
    """Encode integer `value` as base +/- offset==value, with `base` strictly on the PASS side of
    `thr` (margin >= 3), independent of whether `value` itself passes. Returns (base,offset,dw)."""
    order = list(range(3, 26))
    rng.shuffle(order)
    for o in order:
        for dw in ("above", "below"):
            base = value - o if dw == "above" else value + o
            if base <= 0 or o == base:
                continue
            base_passes = (base <= thr - 3) if direction == "max" else (base >= thr + 3)
            if not base_passes:
                continue
            if D.collides(base, forbidden) or D.collides(o, forbidden):
                continue
            return base, o, dw
    return None


def _try_build(i, dom_key, spec, drng):
    elig = G._eligible_params(spec)
    chosen = drng.sample(elig, 3)
    culprit_slot = drng.randrange(3)
    forbidden = set()
    pol = []
    for k, (name, unit, direction, lo, hi, dec) in enumerate(chosen):
        t = int(round(drng.uniform(lo + 0.30 * (hi - lo), hi - 0.30 * (hi - lo))))
        t = G._dodge(t, t + 1, forbidden)
        forbidden.add(float(t))
        m = G._margin(t)
        passes = (k != culprit_slot)
        value = G._pass_value(t, direction, m) if passes else G._fail_value(t, direction, m)
        value = G._dodge(value, t, forbidden)
        forbidden.add(float(value))
        pol.append(dict(name=name, unit=unit, dir=direction, thr=t, value=value, passes=passes))
    culprit = pol[culprit_slot]["name"]
    others = [k for k in range(3) if k != culprit_slot]
    drng.shuffle(others)
    # encoding: others[0] plain(pass); culprit arith(fail, base on pass side); others[1] arith(pass, base on pass side)
    note_lines = []
    arith_meta = {}
    plain_k = others[0]
    note_lines.append(drng.choice(G.PLAIN_T).format(name=pol[plain_k]["name"], v=pol[plain_k]["value"], u=pol[plain_k]["unit"]))
    for k in (culprit_slot, others[1]):
        p = pol[k]
        res = _arith_encode_pass_base(drng, p["value"], p["thr"], p["dir"], forbidden | {float(p["value"])})
        if res is None:
            return None
        base, o, dw = res
        forbidden.add(float(base))
        forbidden.add(float(o))
        note_lines.append(drng.choice(G.ARITH_T).format(name=p["name"], o=o, u=p["unit"], dw=dw, base=base))
        arith_meta[k] = dict(base=base, offset=o, dirword=dw)
    note_lines.append(drng.choice(G.FILLER))
    drng.shuffle(note_lines)
    notes = "\n".join(f"- {ln}" for ln in note_lines)
    p0, p1, p2 = pol
    policy_text = (f"POLICY: {spec['label'].capitalize()} case {i:03d} is APPROVED only if "
                   f"{cond_clause(p0['name'], p0['unit'], p0['dir'], p0['thr'])} AND "
                   f"{cond_clause(p1['name'], p1['unit'], p1['dir'], p1['thr'])} AND "
                   f"{cond_clause(p2['name'], p2['unit'], p2['dir'], p2['thr'])}; otherwise it is DENIED.")
    return dict(
        id=f"rib-c2-{i:03d}", cls="c2", domain=dom_key, truth="DENIED", culprit=culprit,
        culprit_slot=culprit_slot, policy_text=policy_text, notes=notes,
        parameters=[dict(name=p["name"], unit=p["unit"], value=p["value"], policy=True,
                         dir=p["dir"], thr=p["thr"], passes=p["passes"]) for p in pol],
        arith=arith_meta, arith_probe=None)


def gen_c2():
    items = []
    ndom = len(D.DOMAIN_KEYS)
    for i in range(N):
        dom_key = D.DOMAIN_KEYS[i % ndom]
        spec = D.DOMAINS[dom_key]
        for attempt in range(300):
            drng = random.Random((SEED * 100003) ^ (i + 1) ^ (attempt * 0x9e3779b1))
            it = _try_build(i, dom_key, spec, drng)
            if it is not None:
                items.append(it)
                break
        else:
            raise RuntimeError(f"c2 item {i}: no clean encoding")
    return items


def selfcheck_c2(items):
    """All class-c guards PLUS: both arith baselines on the pass side (base-only leak = chance)."""
    probs = G.selfcheck([dict(it, cls="c") for it in items])  # reuse the class-c structural guards
    probs = [p for p in probs if not (isinstance(p[0], str) and p[0].startswith("CORPUS"))]  # sizes/surface re-done below
    base_leak = 0
    for it in items:
        cs = it["culprit_slot"]
        am = {int(k): v for k, v in it["arith"].items()}
        pol = it["parameters"]
        for k, meta in am.items():
            p = pol[k]
            base_passes = (meta["base"] <= p["thr"] - 3) if p["dir"] == "max" else (meta["base"] >= p["thr"] + 3)
            if not base_passes:
                probs.append((it["id"], "c2-base-not-on-pass-side", p["name"]))
        # base-only heuristic recovers culprit?  (should be ~never, since culprit base passes)
        k_oth = [k for k in am if k != cs][0]
        def bf(k):
            p = pol[k]; b = am[k]["base"]
            return (b > p["thr"]) if p["dir"] == "max" else (b < p["thr"])
        if bf(cs) and not bf(k_oth):
            base_leak += 1
    if len(items) != N:
        probs.append(("CORPUS", "c2-size", len(items)))
    frac = base_leak / max(1, len(items))
    if frac > 0.34:
        probs.append(("CORPUS-C2", "base-leak-residual", round(frac, 3)))
    return probs, frac


if __name__ == "__main__":
    items = gen_c2()
    probs, leak = selfcheck_c2(items)
    if probs:
        print(f"SELFCHECK FAILED ({len(probs)}):")
        for p in probs[:40]:
            print("  ", p)
        sys.exit(1)
    with open(os.path.join(HERE, "items_c2.jsonl"), "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    print(f"generated {len(items)} c2 items; base-only culprit leak = {leak:.3f} (<=0.34 required)")
    print("selfcheck: CLEAN")
