#!/usr/bin/env python3
"""B5a fusion-contract pilot — runner + scorer. See prereg_fusion.md.

Two arms at a matched 40-word budget:
  CONTROL  — canonical contract-blind compaction (COMPRESS_SYS[0] wording).
  FUSION   — same + the fusion contract: no evaluative/verdict claim without its deciding
             value in the same clause; if you cannot afford the value, drop the claim.

Per item per arm: compress -> decision -> which. Plus one arm-independent nonotes probe/item.

  python3 runner.py smoke --model grok        # 3 items, both arms, prints raw compaction + probes
  python3 runner.py run   --model grok|haiku|gpt [--limit N]
  python3 runner.py score                      # per-arm/per-model table + predictions pass/fail

Idempotent cache keyed by (model,item,call); temperature 0; hard cap 3000/model. Stdlib only.
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from dissociation import parse_which, wilson  # noqa: E402
from providers import chat, cost_usd          # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
from runner3 import ANS_RE, retained           # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "fusion_results.json")
MODELS = ["grok", "haiku", "gpt"]
W = 40
HARD_CAP = 3000

# ── compaction system prompts (matched budget; FUSION adds the contract) ──────
def control_sys(w):
    return (
        "You are a context compaction engine for an operations assistant. Compress the following "
        f"record to at most {w} words. A future analyst will need to answer questions about it, "
        "but you do not know which questions. Output only the compressed notes.")


def fusion_sys(w):
    return (
        "You are a context compaction engine for an operations assistant. Compress the following "
        f"record to at most {w} words. A future analyst will need to answer questions about it, "
        "but you do not know which questions. FUSION RULE: never state an evaluative or "
        "verdict-bearing claim (e.g. that something is nominal, normal, elevated, out of range, "
        "failing, or fine) without the specific deciding value in the same clause — write 'error "
        "rate 7.2% exceeds the 5% limit', never a bare 'blocked' or 'all nominal'. If you cannot "
        "afford to include the value, drop the claim entirely and keep the value. Output only the "
        "compressed notes.")

# arm -> (system prompt, call-key suffix). 40w = original condition; 15w = tight-budget addendum.
ARMS = {
    "ctrl":   (control_sys(40), "ctrl"),
    "fus":    (fusion_sys(40), "fus"),
    "ctrl15": (control_sys(15), "ctrl15"),
    "fus15":  (fusion_sys(15), "fus15"),
}
# budget label -> (control arm, fusion arm)
BUDGET_PAIRS = {"40w": ("ctrl", "fus"), "15w": ("ctrl15", "fus15")}

DECISION = (" Was the decision APPROVED or DENIED per policy? "
            "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
WHICH = (" If the decision is DENIED, name the single parameter whose reading caused it. "
         "Reply exactly: PARAMETER: <name> or PARAMETER: NONE.")
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
        for sys_prompt, key in ARMS.values():
            summary = api(f"compress_{key}", [{"role": "system", "content": sys_prompt},
                                              {"role": "user", "content": it["document"]}])
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(f"decision_{key}", [{"role": "user", "content": notes + DECISION}])
            api(f"which_{key}", [{"role": "user", "content": notes + WHICH}])
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
        ntxt = g("nonotes") or ""
        nm = ANS_RE.search(ntxt) or __import__("re").search(r"\b(APPROVED|DENIED)\b", ntxt, __import__("re").I)
        rows.append(dict(
            item=it["id"], truth=it["truth"], failing=it["failing_param"],
            realized_words=len(summary.split()),
            fail_retained=(retained(summary, fail["value"]) if fail else None),
            policy_survival=sum(retained(summary, p["value"]) for p in pol) / len(pol),
            decision=decision, decision_correct=(decision == it["truth"]),
            which=wp, which_raw=wraw, which_correct=(wp == (it["failing_param"] or "NONE")),
            which_unmatched=(wp == "UNMATCHED"),
            incoherent=(decision == "DENIED" and wp == "NONE"),
            nn_decision=(nm.group(1).upper() if nm else None)))
    den = [r for r in rows if r["truth"] == "DENIED"]
    lost = [r for r in den if r["fail_retained"] is False]
    kept = [r for r in den if r["fail_retained"] is True]
    dec_acc_all = sum(r["decision_correct"] for r in rows) / len(rows) if rows else None
    dec_acc_D = sum(r["decision_correct"] for r in den) / len(den) if den else None
    which_acc_D = sum(r["which_correct"] for r in den) / len(den) if den else None
    S = sum(r["fail_retained"] for r in den) / len(den) if den else None
    pol_surv = sum(r["policy_survival"] for r in den) / len(den) if den else None
    J = sum(r["decision_correct"] and r["which_correct"] for r in den) / len(den) if den else None
    nn_deny_D = sum(1 for r in den if r["nn_decision"] == "DENIED") / len(den) if den else None
    delta = (dec_acc_D - which_acc_D) if (dec_acc_D is not None and which_acc_D is not None) else None
    return dict(
        n=len(rows), n_denied=len(den), n_lost=len(lost), n_kept=len(kept),
        realized_words=round(sum(r["realized_words"] for r in rows) / len(rows), 2) if rows else None,
        decision_acc=round(dec_acc_all, 4) if dec_acc_all is not None else None,
        decision_acc_D=round(dec_acc_D, 4) if dec_acc_D is not None else None,
        which_acc_D=round(which_acc_D, 4) if which_acc_D is not None else None,
        which_unmatched_D=sum(r["which_unmatched"] for r in den),
        S=round(S, 4) if S is not None else None,
        policy_survival_D=round(pol_surv, 4) if pol_surv is not None else None,
        J=round(J, 4) if J is not None else None,
        delta=round(delta, 4) if delta is not None else None,
        incoherence_D=_cell(sum(r["incoherent"] for r in den), len(den)),
        decision_lost=_cell(sum(r["decision_correct"] for r in lost), len(lost)),
        which_lost=_cell(sum(r["which_correct"] for r in lost), len(lost)),
        incoherence_lost=_cell(sum(r["incoherent"] for r in lost), len(lost)),
        nn_deny_rate_D=round(nn_deny_D, 4) if nn_deny_D is not None else None,
        rows=rows)


REGIME_MIN_LOST = 10  # control-arm shelf-regime guard: >= 10/45 DENIED items lose the witness


def _predictions(c, f):
    """Evaluate P-FU-1..4 for a control/fusion arm pair (both already have rows popped).

    Applicability = shelf-regime guard: the control arm must actually destroy the deciding
    witness on >= REGIME_MIN_LOST DENIED items. A loose budget where witnesses survive (small
    n_lost) has no mirage to collapse and cannot test P-FU-1 (P-FU-1 reported inapplicable)."""
    applicable = c["n_lost"] is not None and c["n_lost"] >= REGIME_MIN_LOST
    p1 = bool(applicable and c["delta"] is not None and c["delta"] > 0.05
              and f["delta"] is not None and f["delta"] <= 0.5 * c["delta"])
    ic_c, ic_f = c["incoherence_D"]["p"], f["incoherence_D"]["p"]
    route_a = bool(ic_c is not None and ic_f is not None and
                   (ic_c == 0.0 and ic_f == 0.0 or (ic_c > 0 and ic_f <= 0.5 * ic_c)))
    dl_c, dl_f, prior = c["decision_lost"]["p"], f["decision_lost"]["p"], c["nn_deny_rate_D"]
    route_b = None
    if None not in (dl_c, dl_f, prior):
        route_b = bool((dl_c - prior) > 0 and (dl_f - prior) <= 0.5 * (dl_c - prior))
    p2 = bool(route_a or route_b)
    rw_c, rw_f = c["realized_words"], f["realized_words"]
    p3 = bool(rw_c is not None and rw_f is not None and rw_f <= 1.25 * rw_c)
    p4 = bool(c["S"] is not None and f["S"] is not None and f["S"] >= c["S"] + 0.15)
    return {
        "P-FU-1_gap_collapse": dict(delta_control=c["delta"], delta_fusion=f["delta"],
                                    control_n_lost=c["n_lost"], regime_min_lost=REGIME_MIN_LOST,
                                    applicable=applicable, passed=p1),
        "P-FU-2_no_unwitnessed_confidence": dict(
            incoherence_control=ic_c, incoherence_fusion=ic_f, route_a=route_a,
            decision_lost_control=dl_c, decision_lost_fusion=dl_f, nonotes_prior=prior,
            route_b=route_b, passed=p2),
        "P-FU-3_length_guard": dict(rw_control=rw_c, rw_fusion=rw_f,
                                    ratio=(round(rw_f / rw_c, 3) if rw_c else None), passed=p3),
        "P-FU-4_survival": dict(S_control=c["S"], S_fusion=f["S"], passed=p4),
    }


def do_score():
    items = load_items()
    cache = load_cache()
    models = [m for m in MODELS if any(k[0] == m for k in cache)]
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]
    out = {"design": dict(nominal_budgets=BUDGET_PAIRS, n_items=len(items),
                          domains=sorted({it["domain"] for it in items}),
                          candidates_disclosed=True),
           "budgets": {}, "cost_usd": {}, "total_cost_usd": 0.0}
    csv_rows = []
    for label, (carm, farm) in BUDGET_PAIRS.items():
        # skip a budget that was not run at all
        if not any((m, it["id"], f"compress_{carm}") in cache for m in models for it in items):
            continue
        per_model = {}
        for alias in models:
            c = score_arm(alias, carm, items, cache)
            f = score_arm(alias, farm, items, cache)
            for arm_label, sc in (("control", c), ("fusion", f)):
                for r in sc["rows"]:
                    csv_rows.append(dict(budget=label, model=alias, arm=arm_label, **r))
            c.pop("rows", None)
            f.pop("rows", None)
            if c["n"] == 0:
                continue
            per_model[alias] = dict(control=c, fusion=f, predictions=_predictions(c, f))
        appl = {m: per_model[m]["predictions"]["P-FU-1_gap_collapse"]["applicable"] for m in per_model}
        p1 = {m: per_model[m]["predictions"]["P-FU-1_gap_collapse"]["passed"] for m in per_model}
        p3 = {m: per_model[m]["predictions"]["P-FU-3_length_guard"]["passed"] for m in per_model}
        collapse_ok = [m for m in per_model if appl[m] and p1[m] and p3[m]]
        n_appl = sum(1 for m in appl if appl[m])
        out["budgets"][label] = dict(
            per_model=per_model,
            verdict=dict(applicable=appl, gap_collapse_models=collapse_ok, n_applicable=n_appl,
                         fusion_collapses_gap=bool(n_appl >= 1 and len(collapse_ok) >= max(1, n_appl))))
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
    hdr = f"{'model/arm':16} {'decD':>6} {'whichD':>7} {'S':>6} {'J':>6} {'Δ':>7} {'incohD':>7} {'rlzW':>6}"
    for label in out["budgets"]:
        b = out["budgets"][label]
        print(f"\n################  BUDGET {label}  ################")
        for alias in models:
            if alias not in b["per_model"]:
                continue
            pm = b["per_model"][alias]
            print(f"\n=== {alias} ({label}) ===")
            print(hdr)
            for arm in ("control", "fusion"):
                a = pm[arm]
                print(f"{alias + '/' + arm:16} {a['decision_acc_D']:>6} {a['which_acc_D']:>7} {a['S']:>6} "
                      f"{a['J']:>6} {a['delta']:>7} {a['incoherence_D']['p']:>7} {a['realized_words']:>6}"
                      f"  (nD={a['n_denied']} lost={a['n_lost']} unm={a['which_unmatched_D']})")
            for k, v in pm["predictions"].items():
                print(f"    {'PASS' if v['passed'] else 'FAIL'}  {k}: "
                      f"{json.dumps({kk: vv for kk, vv in v.items() if kk != 'passed'})}")
        print(f"\n  verdict[{label}]: {json.dumps(b['verdict'])}")
    print(f"\ncost/model: {out['cost_usd']}   total: ${out['total_cost_usd']}   wrote {RESULTS}")


def do_smoke(alias):
    items = load_items()[:3]
    run_model(alias, items)
    cache = load_cache()
    for it in items:
        print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']!r}")
        for _sys, arm in ARMS.values():
            s = cache.get((alias, it["id"], f"compress_{arm}"), {}).get("text", "")
            d = cache.get((alias, it["id"], f"decision_{arm}"), {}).get("text", "")
            w = cache.get((alias, it["id"], f"which_{arm}"), {}).get("text", "")
            print(f"  [{arm}] ({len(s.split())}w) {s.strip()}")
            print(f"       dec: {d.strip()[:40]}   which: {w.strip()[:70]}")
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
