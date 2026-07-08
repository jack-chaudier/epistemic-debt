#!/usr/bin/env python3
"""Real-document external-validity tier — runner + scorer. See prereg_realdoc.md.

Two arms at a matched compaction budget over semi-synthetic REAL-prose items (gen_items.py):
  CONTROL  — canonical contract-blind compaction (signpost-fusion COMPRESS_SYS[0] wording).
  FUSION   — same + the exact fusion contract from signpost-fusion/runner.py.

Models: haiku + gpt (the clean-parser models; grok skipped — acronym parser artifact, confound #2).
Per item per arm: compress -> decision -> WHICH (corrected last-`PARAMETER:` parser). Plus one
arm-independent nonotes prior probe per item.

  python3 runner.py smoke --model haiku      # 3 items, both arms, prints raw compaction + probes
  python3 runner.py run   --model haiku|gpt [--limit N]
  python3 runner.py score                     # per-arm/per-model table + P-RD-1..4 pass/fail

Idempotent cache keyed by (model,item,call); temperature 0; hard cap 2000/model; cost logging.
Stdlib only.
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
from runner3 import ANS_RE, retained           # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "realdoc_results.json")
MODELS = ["haiku", "gpt"]
HARD_CAP = 2000

# ── compaction budget (frozen after smoke; see prereg_realdoc.md) ─────────────
# Fixed nominal 15-word budget on every item — the shelf regime from signpost-fusion (v2), and a
# realistic deployed-compactor spec (fixed budget regardless of input length). Realized length is
# measured and disclosed per arm (the known fusion budget-override).
def budget_words(_item):
    return 15


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

ARMS = {"ctrl": ("control", control_sys), "fus": ("fusion", fusion_sys)}

DECISION = (" Was the decision APPROVED or DENIED per policy? "
            "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
WHICH = (" If the decision is DENIED, name the single parameter whose reading caused it. "
         "Reply exactly: PARAMETER: <name> or PARAMETER: NONE.")
NONOTES = (" Based only on the policy and general plausibility (no case notes), guess: "
           "ANSWER: APPROVED or ANSWER: DENIED.")

REGIME_MIN_LOST = 10  # control-arm shelf-regime guard: >= 10 DENIED items lose the deciding witness


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
        w = budget_words(it)
        for key, (_label, sysfn) in ARMS.items():
            summary = api(f"compress_{key}", [{"role": "system", "content": sysfn(w)},
                                              {"role": "user", "content": it["document"]}])
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(f"decision_{key}", [{"role": "user", "content": notes + DECISION}])
            api(f"which_{key}", [{"role": "user", "content": notes + WHICH}])
        api("nonotes", [{"role": "user", "content": it["policy_text"] + "\n\n" + NONOTES}])
        if (n + 1) % 15 == 0:
            print(f"  {alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


# ── scoring ───────────────────────────────────────────────────────────────────
def _cell(k, n):
    return dict(k=k, n=n, p=(round(k / n, 4) if n else None), ci=wilson(k, n))


def score_arm(alias, arm, items, cache):
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
        nm = ANS_RE.search(ntxt) or re.search(r"\b(APPROVED|DENIED)\b", ntxt, re.I)
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
    app = [r for r in rows if r["truth"] == "APPROVED"]
    dec_acc_all = sum(r["decision_correct"] for r in rows) / len(rows) if rows else None
    dec_acc_D = sum(r["decision_correct"] for r in den) / len(den) if den else None
    which_acc_D = sum(r["which_correct"] for r in den) / len(den) if den else None
    S = sum(r["fail_retained"] for r in den) / len(den) if den else None
    J = sum(r["decision_correct"] and r["which_correct"] for r in den) / len(den) if den else None
    nn_deny_D = sum(1 for r in den if r["nn_decision"] == "DENIED") / len(den) if den else None
    nn_deny_A = sum(1 for r in app if r["nn_decision"] == "DENIED") / len(app) if app else None
    delta = (dec_acc_D - which_acc_D) if (dec_acc_D is not None and which_acc_D is not None) else None
    return dict(
        n=len(rows), n_denied=len(den), n_lost=len(lost), n_kept=len(kept), n_approved=len(app),
        realized_words=round(sum(r["realized_words"] for r in rows) / len(rows), 2) if rows else None,
        decision_acc=round(dec_acc_all, 4) if dec_acc_all is not None else None,
        decision_acc_A=round(sum(r["decision_correct"] for r in app) / len(app), 4) if app else None,
        decision_acc_D=round(dec_acc_D, 4) if dec_acc_D is not None else None,
        which_acc_D=round(which_acc_D, 4) if which_acc_D is not None else None,
        which_unmatched_D=sum(r["which_unmatched"] for r in den),
        S=round(S, 4) if S is not None else None,
        J=round(J, 4) if J is not None else None,
        delta=round(delta, 4) if delta is not None else None,
        incoherence_D=_cell(sum(r["incoherent"] for r in den), len(den)),
        decision_lost=_cell(sum(r["decision_correct"] for r in lost), len(lost)),
        which_lost=_cell(sum(r["which_correct"] for r in lost), len(lost)),
        nn_deny_rate_D=round(nn_deny_D, 4) if nn_deny_D is not None else None,
        nn_deny_rate_A=round(nn_deny_A, 4) if nn_deny_A is not None else None,
        rows=rows)


def _predictions(c, f):
    """P-RD-1..4 for a control/fusion pair. Applicability = shelf-regime guard on the CONTROL arm."""
    applicable = c["n_lost"] is not None and c["n_lost"] >= REGIME_MIN_LOST
    # P-RD-1 dissociation replicates: control Δ >= 0.20 (given regime guard)
    p1 = bool(applicable and c["delta"] is not None and c["delta"] >= 0.20)
    # P-RD-2 incoherence appears in control: >= 0.05
    ic_c, ic_f = c["incoherence_D"]["p"], f["incoherence_D"]["p"]
    p2 = bool(applicable and ic_c is not None and ic_c >= 0.05)
    # P-RD-3 fusion kills incoherence: <= 0.5 * control (0 counts as pass whenever control > 0;
    # if control incoherence is already ~0 the shelf did not form -> inapplicable via the guard)
    p3 = bool(applicable and ic_c is not None and ic_f is not None and ic_c > 0 and ic_f <= 0.5 * ic_c)
    # P-RD-4 witness survival lift: S(fusion) >= S(control) + 0.15
    p4 = bool(c["S"] is not None and f["S"] is not None and f["S"] >= c["S"] + 0.15)
    rw_c, rw_f = c["realized_words"], f["realized_words"]
    return {
        "applicable_regime_guard": dict(control_n_lost=c["n_lost"], min_lost=REGIME_MIN_LOST,
                                        applicable=applicable),
        "P-RD-1_dissociation": dict(delta_control=c["delta"], dec_D=c["decision_acc_D"],
                                    which_D=c["which_acc_D"], threshold=0.20, passed=p1),
        "P-RD-2_incoherence": dict(incoherence_control=ic_c, threshold=0.05, passed=p2),
        "P-RD-3_fusion_kills": dict(incoherence_control=ic_c, incoherence_fusion=ic_f, passed=p3),
        "P-RD-4_survival": dict(S_control=c["S"], S_fusion=f["S"], passed=p4),
        "realized_length_ratio": dict(rw_control=rw_c, rw_fusion=rw_f,
                                      ratio=(round(rw_f / rw_c, 3) if rw_c else None)),
    }


def do_score():
    items = load_items()
    cache = load_cache()
    models = [m for m in MODELS if any(k[0] == m for k in cache)]
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]
    out = dict(design=dict(n_items=len(items), domain=DOMAIN_LABEL(items), budget="fixed 15 words",
                           candidates_disclosed=True, models=models,
                           n_sources=len({it["source_id"] for it in items})),
               per_model={}, cost_usd={}, total_cost_usd=0.0)
    csv_rows = []
    for alias in models:
        c = score_arm(alias, "ctrl", items, cache)
        f = score_arm(alias, "fus", items, cache)
        for arm_label, sc in (("control", c), ("fusion", f)):
            for r in sc["rows"]:
                csv_rows.append(dict(model=alias, arm=arm_label, **r))
        c.pop("rows", None)
        f.pop("rows", None)
        if c["n"] == 0:
            continue
        out["per_model"][alias] = dict(control=c, fusion=f, predictions=_predictions(c, f))
    out["cost_usd"] = {m: round(cost_usd(m, tok[m]), 4) for m in models}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    if csv_rows:
        with open(os.path.join(HERE, "scored.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(csv_rows[0].keys()))
            w.writeheader()
            w.writerows(csv_rows)
    _print(out, models)


def DOMAIN_LABEL(items):
    return items[0]["domain"] if items else "?"


def _print(out, models):
    hdr = f"{'model/arm':16} {'decD':>6} {'whichD':>7} {'S':>6} {'J':>6} {'Δ':>7} {'incohD':>7} {'rlzW':>6}"
    for alias in models:
        if alias not in out["per_model"]:
            continue
        pm = out["per_model"][alias]
        print(f"\n=== {alias} ===")
        print(hdr)
        for arm in ("control", "fusion"):
            a = pm[arm]
            print(f"{alias + '/' + arm:16} {a['decision_acc_D']:>6} {a['which_acc_D']:>7} {a['S']:>6} "
                  f"{a['J']:>6} {a['delta']:>7} {a['incoherence_D']['p']:>7} {a['realized_words']:>6}"
                  f"  (nD={a['n_denied']} lost={a['n_lost']} unm={a['which_unmatched_D']} "
                  f"decA={a['decision_acc_A']} nnDenyD={a['nn_deny_rate_D']})")
        for k, v in pm["predictions"].items():
            tag = "PASS" if v.get("passed") else ("    " if "passed" not in v else "FAIL")
            print(f"    {tag}  {k}: {json.dumps({kk: vv for kk, vv in v.items() if kk != 'passed'})}")
    print(f"\ncost/model: {out['cost_usd']}   total: ${out['total_cost_usd']}   wrote {RESULTS}")


def do_smoke(alias):
    items = load_items()[:3]
    run_model(alias, items)
    cache = load_cache()
    for it in items:
        print(f"\n--- {it['id']} truth={it['truth']} failing={it['failing_param']!r} "
              f"src={it['source_id']} docwords={it['word_count']}")
        print(f"    POLICY: {it['policy_text'][:200]}")
        for key, (label, _fn) in ARMS.items():
            s = cache.get((alias, it["id"], f"compress_{key}"), {}).get("text", "")
            d = cache.get((alias, it["id"], f"decision_{key}"), {}).get("text", "")
            w = cache.get((alias, it["id"], f"which_{key}"), {}).get("text", "")
            print(f"  [{label}] ({len(s.split())}w) {s.strip()}")
            print(f"       dec: {d.strip()[:40]}   which: {w.strip()[:80]}")
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
