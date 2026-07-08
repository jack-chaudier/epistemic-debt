#!/usr/bin/env python3
"""B1 certificate-compaction pilot — runner + scorer. See prereg_certificates.md.

Four compaction arms at a matched 15-word nominal budget (the shelf regime, per the
highpower/domains + signpost-fusion campaigns):

  ctrl  CONTROL          — canonical contract-blind plain compaction (doc only).
  vd    VALUEDENSE       — blind H.2 names+numbers+units instruction (doc only).
  vda   VALUEDENSE_AWARE — policy-aware, store every policy-relevant reading (policy + doc).
                           The matched-policy-access format control for the certificate quotient.
  cert  CERTIFICATE      — policy-aware cooperative writer: claim + single deciding-value
                           certificate + pointer (policy + doc).

Rationale (the certificate-quotient analog, honesty_theorem.py 9 vs 13 states): value-dense
stores the whole witness set (all candidate values, the joint quotient); the certificate stores
only the deciding value + a pointer to the rest (the cheaper certificate quotient). The claim is
that the certificate licenses calibrated reader behavior (verdict + reason + abstention) at
FEWER realized words. The certificate needs the policy to know which value decides, so cert/vda
are policy-aware; ctrl/vd are the blind deployed baselines. Policy access is disclosed per arm.

Per item per arm: compress -> decision -> which -> which_abstain. Plus one nonotes probe/item.

  python3 runner.py smoke --model grok        # 3 items, all arms, prints raw compaction + probes
  python3 runner.py run   --model grok|haiku|gpt [--limit N]
  python3 runner.py score                      # per-arm/per-model table + predictions pass/fail

Idempotent cache keyed by (model,item,call); temperature 0; hard cap 3000/model. Stdlib only.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from dissociation import parse_which, wilson  # noqa: E402
from providers import chat, cost_usd          # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
from runner3 import ANS_RE, NUM_RE, retained    # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "certificate_results.json")
MODELS = ["grok", "haiku", "gpt"]
W = 15
HARD_CAP = 3000


# ── compaction system prompts (matched 15-word nominal budget) ────────────────
def control_sys(w):
    return (
        "You are a context compaction engine for an operations assistant. Compress the following "
        f"record to at most {w} words. A future analyst will need to answer questions about it, "
        "but you do not know which questions. Output only the compressed notes.")


def valuedense_sys(w):
    return (
        "You are a context compaction engine for an operations assistant. Compress the following "
        f"record to at most {w} words — a hard limit (a reading like 'wind 11.1 m/s' counts as 3 "
        "words). A future analyst will need to answer questions about it, but you do not know "
        "which questions. Spend the budget on concrete parameter readings (name, number, unit) "
        "rather than prose, keeping the readings most likely to decide any pass/fail or threshold "
        "question; if they do not all fit, keep only the most decision-relevant few. Output only "
        "the compressed notes.")


def valuedense_aware_sys(w):
    # matched policy-access control: same value-density goal, but the writer holds the policy.
    return (
        "You are a context compaction engine for an operations assistant. The future analyst who "
        "reads your notes will hold the POLICY below but not this record. Compress the record to "
        f"at most {w} words — a hard limit (a reading like 'wind 11.1 m/s' counts as 3 words). "
        "Spend the budget on the concrete policy-relevant readings (name, number, unit) so any "
        "threshold question in the policy can be answered; keep as many decision-relevant readings "
        "as fit. Output only the compressed notes.")


def certificate_sys(w):
    # policy-aware certificate writer: claim + single deciding value + pointer. Terse by
    # instruction so the format has a fair shot at the word economy (smoke-iterated, then frozen).
    return (
        "You are a context compaction engine for an operations assistant, writing for a future "
        "analyst who will hold the POLICY below but not this record. Compress the record to at "
        f"most {w} words as a terse CERTIFICATE, no prose, in three parts: "
        "(1) the decision the policy reaches on this record — APPROVED or DENIED; "
        "(2) its certificate — for DENIED, ONLY the single policy reading that fails, as "
        "'name number unit vs threshold'; for APPROVED, just 'all criteria met'; "
        "(3) a pointer: 'other readings not included — see source'. "
        "Do not list any non-deciding reading. Output only the certificate.")


# arm key -> (builds messages from item). Aware arms prepend the policy; blind arms send the doc.
def _blind_msgs(sys_prompt, it):
    return [{"role": "system", "content": sys_prompt},
            {"role": "user", "content": it["document"]}]


def _aware_msgs(sys_prompt, it):
    return [{"role": "system", "content": sys_prompt},
            {"role": "user", "content": "POLICY:\n" + it["policy_text"]
             + "\n\nRECORD:\n" + it["document"]}]


ARMS = {
    "ctrl": dict(sys=control_sys(W), aware=False),
    "vd":   dict(sys=valuedense_sys(W), aware=False),
    "vda":  dict(sys=valuedense_aware_sys(W), aware=True),
    "cert": dict(sys=certificate_sys(W), aware=True),
}
ARM_ORDER = ["ctrl", "vd", "vda", "cert"]

DECISION = (" Was the decision APPROVED or DENIED per policy? "
            "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
WHICH = (" If the decision is DENIED, name the single parameter whose reading caused it. "
         "Reply exactly: PARAMETER: <name> or PARAMETER: NONE.")
ABSTAIN_ADD = (" If the notes do not contain enough information to determine which parameter, "
               "reply exactly: PARAMETER: INSUFFICIENT_EVIDENCE.")
NONOTES = (" Based only on the policy and general plausibility (no case notes), guess: "
           "ANSWER: APPROVED or ANSWER: DENIED.")


def load_items():
    path = os.path.join(HERE, "items.jsonl")
    if not os.path.exists(path):
        sys.exit("items.jsonl missing — run gen_items.py first")
    return [json.loads(l) for l in open(path)]


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def run_model(alias, items):
    cache = load_cache()
    n0 = len(cache)

    def api(call, messages):
        key = (alias, iid, call)
        if key in cache:
            return cache[key]["text"]
        if len(cache) - n0 + 1 > HARD_CAP:
            sys.exit(f"HARD CAP {HARD_CAP} reached for {alias}")
        text, usage = chat(alias, messages)
        rec = dict(model=alias, item=iid, call=call, text=text, usage=usage)
        with open(RAW, "a") as f:
            f.write(json.dumps(rec) + "\n")
        cache[key] = rec
        return text

    for n, it in enumerate(items):
        iid = it["id"]
        for arm in ARM_ORDER:
            spec = ARMS[arm]
            msgs = (_aware_msgs if spec["aware"] else _blind_msgs)(spec["sys"], it)
            summary = api(f"compress_{arm}", msgs)
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(f"decision_{arm}", [{"role": "user", "content": notes + DECISION}])
            api(f"which_{arm}", [{"role": "user", "content": notes + WHICH}])
            api(f"whichab_{arm}", [{"role": "user", "content": notes + WHICH + ABSTAIN_ADD}])
        api("nonotes", [{"role": "user", "content": it["policy_text"] + "\n\n" + NONOTES}])
        if (n + 1) % 20 == 0:
            print(f"  {alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


# ── scoring ───────────────────────────────────────────────────────────────────
def _cell(k, n):
    return dict(k=k, n=n, p=(round(k / n, 4) if n else None), ci=wilson(k, n))


def score_arm(alias, arm, items, cache):
    """Return per-arm metrics + per-item rows for one (model, arm)."""
    rows = []
    for it in items:
        g = lambda call: cache.get((alias, it["id"], call), {}).get("text")
        summary = g(f"compress_{arm}")
        if summary is None:
            continue
        pol = [p for p in it["parameters"] if p["policy"]]
        fail = next((p for p in pol if not p["passes"]), None)
        dtxt = g(f"decision_{arm}") or ""
        m = ANS_RE.search(dtxt)
        decision = m.group(1).upper() if m else None
        wp, wraw = parse_which(g(f"which_{arm}"), it["parameters"])
        wa, waraw = parse_which(g(f"whichab_{arm}"), it["parameters"])
        ntxt = g("nonotes") or ""
        nm = ANS_RE.search(ntxt) or re.search(r"\b(APPROVED|DENIED)\b", ntxt, re.I)
        target = it["failing_param"] or "NONE"
        rows.append(dict(
            item=it["id"], domain=it["domain"], truth=it["truth"], failing=it["failing_param"],
            realized_words=len(summary.split()),
            n_values=len(NUM_RE.findall(summary)),
            fail_retained=(retained(summary, fail["value"]) if fail else None),
            policy_survival=sum(retained(summary, p["value"]) for p in pol) / len(pol),
            decision=decision, decision_correct=(decision == it["truth"]),
            which=wp, which_raw=wraw, which_correct=(wp == target),
            which_unmatched=(wp == "UNMATCHED"),
            whichab=wa, whichab_raw=waraw,
            whichab_correct=(wa == target),
            whichab_abstain=(wa == "INSUFFICIENT_EVIDENCE"),
            whichab_none=(wa == "NONE"),
            incoherent=(decision == "DENIED" and wp == "NONE"),
            nn_decision=(nm.group(1).upper() if nm else None)))
    den = [r for r in rows if r["truth"] == "DENIED"]
    app = [r for r in rows if r["truth"] == "APPROVED"]
    lost = [r for r in den if r["fail_retained"] is False]
    kept = [r for r in den if r["fail_retained"] is True]
    frac = lambda sel, sub: (round(sum(bool(x) for x in (r[sel] for r in sub)) / len(sub), 4)
                             if sub else None)
    dec_acc_all = frac("decision_correct", rows)
    dec_acc_D = frac("decision_correct", den)
    which_acc_D = frac("which_correct", den)
    S = frac("fail_retained", den)
    pol_surv = round(sum(r["policy_survival"] for r in den) / len(den), 4) if den else None
    J = round(sum(r["decision_correct"] and r["which_correct"] for r in den) / len(den), 4) if den else None
    nn_deny_D = round(sum(1 for r in den if r["nn_decision"] == "DENIED") / len(den), 4) if den else None
    delta = (dec_acc_D - which_acc_D) if (dec_acc_D is not None and which_acc_D is not None) else None
    return dict(
        n=len(rows), n_denied=len(den), n_approved=len(app), n_lost=len(lost), n_kept=len(kept),
        realized_words=round(sum(r["realized_words"] for r in rows) / len(rows), 2) if rows else None,
        n_values=round(sum(r["n_values"] for r in rows) / len(rows), 2) if rows else None,
        decision_acc=dec_acc_all, decision_acc_D=dec_acc_D,
        which_acc_D=which_acc_D, which_unmatched_D=sum(r["which_unmatched"] for r in den),
        S=S, policy_survival_D=pol_surv, J=J, delta=round(delta, 4) if delta is not None else None,
        incoherence_D=_cell(sum(r["incoherent"] for r in den), len(den)),
        # abstention calibration (WHICH-abstain probe)
        approved_none=_cell(sum(r["whichab_none"] for r in app), len(app)),
        approved_false_abstain=_cell(sum(r["whichab_abstain"] for r in app), len(app)),
        approved_confab=_cell(sum(not r["whichab_none"] and not r["whichab_abstain"]
                                  and r["whichab"] not in (None, "UNMATCHED") for r in app), len(app)),
        lost_abstain=_cell(sum(r["whichab_abstain"] for r in lost), len(lost)),
        lost_confab=_cell(sum(not r["whichab_abstain"] and not r["whichab_correct"]
                              and r["whichab"] not in (None, "NONE", "UNMATCHED") for r in lost), len(lost)),
        kept_which_correct=_cell(sum(r["which_correct"] for r in kept), len(kept)),
        nn_deny_rate_D=nn_deny_D,
        rows=rows)


REGIME_MIN_LOST = 10  # control-arm shelf-regime guard: >= 10/45 DENIED items lose the witness


def _predictions(arms):
    """Evaluate P-CE-1..4 from the per-arm score dicts (rows already popped)."""
    ctrl, vd, vda, cert = (arms[k] for k in ARM_ORDER)
    applicable = ctrl["n_lost"] is not None and ctrl["n_lost"] >= REGIME_MIN_LOST

    # P-CE-1 (certificate quotient, matched policy access): cert non-inferior to vda on J AND
    # strictly fewer realized words. The clean 9-vs-13 analog.
    p1 = bool(cert["J"] is not None and vda["J"] is not None and cert["realized_words"] is not None
              and vda["realized_words"] is not None
              and cert["J"] >= vda["J"] - 0.05
              and cert["realized_words"] < vda["realized_words"])

    # P-CE-1b (team-lead literal): cert vs blind value-dense — J non-inferior at <= words.
    p1b = bool(cert["J"] is not None and vd["J"] is not None
               and cert["J"] >= vd["J"] - 0.05
               and cert["realized_words"] <= vd["realized_words"])

    # P-CE-2 (abstention calibrated): on APPROVED items cert says NONE, false-abstain <= 0.10.
    fa = cert["approved_false_abstain"]["p"]
    none_ok = cert["approved_none"]["p"]
    p2 = bool(fa is not None and fa <= 0.10 and none_ok is not None and none_ok >= 0.90)

    # P-CE-3 (beats control on J by >= 0.20 in shelf regime).
    p3 = bool(applicable and cert["J"] is not None and ctrl["J"] is not None
              and (cert["J"] - ctrl["J"]) >= 0.20)

    # P-CE-4 (economy, core): cert realized words <= both value-dense arms.
    p4 = bool(cert["realized_words"] is not None and vd["realized_words"] is not None
              and vda["realized_words"] is not None
              and cert["realized_words"] <= vd["realized_words"]
              and cert["realized_words"] <= vda["realized_words"])

    return {
        "P-CE-1_certificate_quotient": dict(
            J_cert=cert["J"], J_vda=vda["J"], rw_cert=cert["realized_words"],
            rw_vda=vda["realized_words"], passed=p1),
        "P-CE-1b_vs_blind_valuedense": dict(
            J_cert=cert["J"], J_vd=vd["J"], rw_cert=cert["realized_words"],
            rw_vd=vd["realized_words"], passed=p1b),
        "P-CE-2_abstention_calibrated": dict(
            approved_none=none_ok, approved_false_abstain=fa,
            approved_confab=cert["approved_confab"]["p"], passed=p2),
        "P-CE-3_beats_control": dict(
            J_cert=cert["J"], J_ctrl=ctrl["J"], ctrl_n_lost=ctrl["n_lost"],
            regime_min_lost=REGIME_MIN_LOST, applicable=applicable, passed=p3),
        "P-CE-4_word_economy": dict(
            rw_cert=cert["realized_words"], rw_vd=vd["realized_words"],
            rw_vda=vda["realized_words"], passed=p4),
    }


def do_score():
    items = load_items()
    cache = load_cache()
    models = [m for m in MODELS if any(k[0] == m for k in cache)]
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]
    out = {"design": dict(budget_words=W, arms=ARM_ORDER, n_items=len(items),
                          domains=sorted({it["domain"] for it in items}),
                          policy_aware={a: ARMS[a]["aware"] for a in ARM_ORDER},
                          candidates_disclosed=True),
           "per_model": {}, "cost_usd": {}, "total_cost_usd": 0.0}
    csv_rows = []
    for alias in models:
        scored = {}
        for arm in ARM_ORDER:
            sc = score_arm(alias, arm, items, cache)
            for r in sc["rows"]:
                csv_rows.append(dict(model=alias, arm=arm, **r))
            sc.pop("rows", None)
            scored[arm] = sc
        if scored["ctrl"]["n"] == 0:
            continue
        out["per_model"][alias] = dict(arms=scored, predictions=_predictions(scored))
    out["cost_usd"] = {m: round(cost_usd(m, tok[m]), 4) for m in models}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    if csv_rows:
        cols = list(csv_rows[0].keys())
        with open(os.path.join(HERE, "scored.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(csv_rows)
    _print(out, models)


def _print(out, models):
    hdr = (f"{'arm':6} {'decD':>6} {'whichD':>7} {'S':>6} {'J':>6} {'Δ':>7} "
           f"{'rlzW':>6} {'#val':>5} {'appNONE':>8} {'appFA':>7} {'lostAbs':>8}")
    for alias in models:
        if alias not in out["per_model"]:
            continue
        pm = out["per_model"][alias]
        print(f"\n=== {alias} ===")
        print(hdr)
        for arm in ARM_ORDER:
            a = pm["arms"][arm]
            print(f"{arm:6} {a['decision_acc_D']!s:>6} {a['which_acc_D']!s:>7} {a['S']!s:>6} "
                  f"{a['J']!s:>6} {a['delta']!s:>7} {a['realized_words']!s:>6} {a['n_values']!s:>5} "
                  f"{a['approved_none']['p']!s:>8} {a['approved_false_abstain']['p']!s:>7} "
                  f"{a['lost_abstain']['p']!s:>8}  (nD={a['n_denied']} lost={a['n_lost']} "
                  f"unm={a['which_unmatched_D']})")
        for k, v in pm["predictions"].items():
            print(f"    {'PASS' if v['passed'] else 'FAIL'}  {k}: "
                  f"{json.dumps({kk: vv for kk, vv in v.items() if kk != 'passed'})}")
    print(f"\ncost/model: {out['cost_usd']}   total: ${out['total_cost_usd']}   wrote {RESULTS}")


def do_smoke(alias):
    items = load_items()[:3]
    run_model(alias, items)
    cache = load_cache()
    for it in items:
        print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']!r}")
        for arm in ARM_ORDER:
            s = cache.get((alias, it["id"], f"compress_{arm}"), {}).get("text", "")
            d = cache.get((alias, it["id"], f"decision_{arm}"), {}).get("text", "")
            w = cache.get((alias, it["id"], f"which_{arm}"), {}).get("text", "")
            wa = cache.get((alias, it["id"], f"whichab_{arm}"), {}).get("text", "")
            print(f"  [{arm}] ({len(s.split())}w) {s.strip()}")
            print(f"       dec:{d.strip()[:34]}  which:{w.strip()[:46]}  ab:{wa.strip()[:46]}")
        nn = cache.get((alias, it["id"], "nonotes"), {}).get("text", "")
        print(f"  [nonotes] {nn.strip()[:40]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    if a.cmd == "smoke":
        do_smoke(a.model)
        return
    items = load_items()
    if a.limit:
        items = items[:a.limit]
    run_model(a.model, items)
    print(f"{a.model} done ({len(items)} items)")


if __name__ == "__main__":
    main()
