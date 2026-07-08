#!/usr/bin/env python3
"""R1 — Δ-audit of vanilla RLM: runner + scorer. See prereg_rlm_audit.md.

Three conditions over the SAME long-context items (gen_items.py), same root model:
  (a) naive   — NAIVE-COMPACTION baseline: the whole multi-doc context is compressed to a fixed
                budget, then the decision + WHICH probe (the row-27/31 shelf pattern).
  (b) vanilla — VANILLA RLM: the root recursively sub-queries slices; sub-readers return free-form
                findings (rlm_loop.py, condition "vanilla").
  (c) cert    — CERT-PROMPTED RLM: identical loop, sub-readers return the certificate contract and
                the root must cite the witness chain or name the missing value (condition "cert").

Instruments BOTH layers: final answers (decision/WHICH/J/Δ/incoherence) AND the sub-call return
channel (does the deciding witness value survive into the root's window — "relocated compaction").

  python3 runner.py smoke --model gpt          # 3 items × 3 conditions; prints traces + returns
  python3 runner.py run   --model gpt|haiku [--limit N]
  python3 runner.py score                       # per-condition table + P-R1-1..4 pass/fail

Idempotent cache keyed by (model,item,call); temperature 0; hard cap 4000/model; cost logging.
RLM calls replay deterministically from cache at score time. Stdlib only.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, HERE)
from providers import chat, cost_usd              # noqa: E402
from runner3 import ANS_RE, retained, match_param  # noqa: E402
from rlm_loop import run_rlm, SUB_WORDS, MAX_SUB   # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "rlm_audit_results.json")
MODELS = ["gpt", "haiku"]
HARD_CAP = 4000
CONDITIONS = ["naive", "vanilla", "cert"]

# naive budget: matched to the RLM root's realized return budget (a few sub-returns), so the
# baseline is the same output bottleneck WITHOUT slice addressing. Frozen after smoke.
NAIVE_WORDS = 150


def naive_sys(w):
    return ("You are a context compaction engine for an operations assistant. The following is a "
            f"collection of case files. Compress ALL of it to at most {w} words. A future analyst "
            "will need to answer a policy question about ONE of these cases, but you do not know "
            "which case or which question. Output only the compressed notes.")


DECISION = (" Was the decision APPROVED or DENIED per policy? "
            "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
WHICH = (" If the decision is DENIED, name the single parameter whose reading caused it. "
         "Reply exactly: PARAMETER: <name> or PARAMETER: NONE.")
NONOTES = (" Based only on the policy and general plausibility (no case notes), guess: "
           "ANSWER: APPROVED or ANSWER: DENIED.")

_PARAM_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)


def parse_which_flat(text):
    """Naive-arm WHICH parser (last PARAMETER: anchor); returns label in scorer vocabulary."""
    m = _PARAM_RE.findall(text or "")
    if not m:
        return None
    raw = m[-1].strip().rstrip(".")
    up = raw.upper()
    if up.startswith("NONE"):
        return "NONE"
    if "INSUFFICIENT" in up or "MISSING" in up:
        return "MISSING"
    return raw  # resolved to a param name by the caller via match_param


def load_items():
    path = os.path.join(HERE, "items.jsonl")
    if not os.path.exists(path):
        sys.exit("items.jsonl missing — run gen_items.py first")
    return [json.loads(l) for l in open(path) if l.strip()]


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def big_document(item):
    return "\n\n----------\n\n".join(
        f"[slice {s['slice_id']}] {s['document']}" for s in item["slices"])


def run_model(alias, items):
    cache = load_cache()
    n0 = len(cache)
    state = {"iid": None}

    def api(call, messages):
        key = (alias, state["iid"], call)
        if key in cache:
            return cache[key]["text"]
        if len(cache) - n0 + 1 > HARD_CAP:
            sys.exit(f"HARD CAP {HARD_CAP} reached for {alias}")
        text, usage = chat(alias, messages)
        rec = dict(model=alias, item=state["iid"], call=call, text=text, usage=usage)
        with open(RAW, "a") as f:
            f.write(json.dumps(rec) + "\n")
        cache[key] = rec
        return text

    for n, it in enumerate(items):
        state["iid"] = it["id"]
        # (a) naive compaction of the whole context
        notes = api("naive_compress", [{"role": "system", "content": naive_sys(NAIVE_WORDS)},
                                       {"role": "user", "content": big_document(it)}])
        probe = it["policy_text"] + "\n\nCompressed case notes:\n" + notes + "\n\n"
        api("naive_decision", [{"role": "user", "content": probe + DECISION}])
        api("naive_which", [{"role": "user", "content": probe + WHICH}])
        # (b) vanilla RLM  (c) cert-prompted RLM
        run_rlm(api, it, "vanilla", match_param)
        run_rlm(api, it, "cert", match_param)
        # shared prior probe
        api("nonotes", [{"role": "user", "content": it["policy_text"] + "\n\n" + NONOTES}])
        if (n + 1) % 5 == 0:
            print(f"  {alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


# ── scoring ───────────────────────────────────────────────────────────────────
def _cache_api(alias, cache):
    """Read-only api that replays a cached RLM trace (returns None on miss — no new calls)."""
    state = {"iid": None}

    def api(call, messages):
        r = cache.get((alias, state["iid"], call))
        return r["text"] if r else None
    return api, state


def score_rows(alias, items, cache):
    """One row per (item, condition). Replays RLM traces from cache."""
    api, state = _cache_api(alias, cache)
    rows = []
    for it in items:
        iid = it["id"]
        pol = [p for p in it["parameters"] if p.get("policy")]
        fail = next((p for p in pol if not p["passes"]), None)
        target = it["failing_param"] or "NONE"

        # (a) naive
        notes = cache.get((alias, iid, "naive_compress"), {}).get("text")
        if notes is not None:
            dtxt = cache.get((alias, iid, "naive_decision"), {}).get("text") or ""
            m = ANS_RE.search(dtxt)
            decision = m.group(1).upper() if m else None
            wraw = parse_which_flat(cache.get((alias, iid, "naive_which"), {}).get("text"))
            which = ("NONE" if wraw in ("NONE", "MISSING", None)
                     else (match_param(wraw, it["parameters"]) or "UNMATCHED"))
            if wraw == "MISSING":
                which = "MISSING"
            rows.append(_row(it, "naive", decision, which, target, fail,
                             fail_retained=(retained(notes, fail["value"]) if fail else None),
                             touched_relevant=None, n_sub=0, ret_words=len(notes.split()),
                             gave_up=False))

        # (b),(c) RLM conditions
        for cond in ("vanilla", "cert"):
            if (alias, iid, f"{cond}_root_0") not in cache:
                continue
            state["iid"] = iid
            tr = run_rlm(api, it, cond, match_param)
            rel_subs = [sc for sc in tr["subcalls"] if sc["is_relevant"]]
            witness_in_returns = (fail is not None and
                                  any(retained(sc["ret"] or "", fail["value"]) for sc in rel_subs))
            ret_words = ([sc["ret_words"] for sc in tr["subcalls"]] or [0])
            rows.append(_row(it, cond, tr["decision"], tr["parameter"], target, fail,
                             fail_retained=(witness_in_returns if fail else None),
                             touched_relevant=bool(rel_subs), n_sub=tr["n_sub"],
                             ret_words=round(sum(ret_words) / len(ret_words), 1),
                             gave_up=tr["gave_up"]))
    return rows


def _row(it, cond, decision, which, target, fail, fail_retained, touched_relevant,
         n_sub, ret_words, gave_up):
    return dict(
        item=it["id"], arm=it["arm"], condition=cond, truth=it["truth"],
        failing=it["failing_param"], decision=decision, decision_correct=(decision == it["truth"]),
        which=which, which_correct=(which == target),
        incoherent=(decision == "DENIED" and which == "NONE"),
        named_gap=(which == "MISSING"), fail_retained=fail_retained,
        touched_relevant=touched_relevant, n_sub=n_sub, ret_words=ret_words, gave_up=gave_up)


def _agg(rows):
    """Aggregate a set of rows (one condition, one arm-or-pooled) into the metric block."""
    den = [r for r in rows if r["truth"] == "DENIED"]
    app = [r for r in rows if r["truth"] == "APPROVED"]
    lost = [r for r in den if r["fail_retained"] is False]
    frac = lambda xs: (round(sum(bool(x) for x in xs) / len(xs), 4) if xs else None)
    dec_D = frac([r["decision_correct"] for r in den])
    which_D = frac([r["which_correct"] for r in den])
    S = frac([r["fail_retained"] for r in den if r["fail_retained"] is not None])
    J = frac([r["decision_correct"] and r["which_correct"] for r in den])
    delta = (round(dec_D - which_D, 4) if (dec_D is not None and which_D is not None) else None)
    touched = [r for r in den if r["touched_relevant"]]
    # P-R1-2 channel: witness survival through returns, on DENIED items that touched the relevant doc
    ret_surv = frac([r["fail_retained"] for r in touched]) if touched else None
    return dict(
        n=len(rows), n_denied=len(den), n_approved=len(app), n_lost=len(lost),
        decision_acc=frac([r["decision_correct"] for r in rows]),
        decision_acc_A=frac([r["decision_correct"] for r in app]),
        decision_acc_D=dec_D, which_acc_D=which_D, S=S, J=J, delta=delta,
        incoherence_D=frac([r["incoherent"] for r in den]),
        named_gap_D=frac([r["named_gap"] for r in den]),
        touched_relevant_D=frac([r["touched_relevant"] for r in den]) if any(
            r["touched_relevant"] is not None for r in den) else None,
        witness_survival_returns=ret_surv, n_touched_D=len(touched),
        ret_words=round(sum(r["ret_words"] for r in rows) / len(rows), 1) if rows else None,
        gave_up=frac([r["gave_up"] for r in rows]),
        n_sub=round(sum(r["n_sub"] for r in rows) / len(rows), 2) if rows else None)


REGIME_MIN_LOST = 6  # vanilla-RLM shelf-regime guard for the cert-halving prediction


def _predictions(pool):
    """P-R1-1..4 on the pooled (both-arm) metrics for one model."""
    a, b, c = pool["naive"], pool["vanilla"], pool["cert"]
    # P-R1-1 RLM final decision accuracy >= naive compaction
    p1 = bool(b["decision_acc"] is not None and a["decision_acc"] is not None
              and b["decision_acc"] >= a["decision_acc"])
    # P-R1-2 witness survival through FREE-FORM returns < 0.5 (on DENIED items touching relevant doc)
    ws = b["witness_survival_returns"]
    p2 = bool(ws is not None and b["n_touched_D"] >= REGIME_MIN_LOST and ws < 0.5)
    # P-R1-4 cert halves Δ AND incoherence vs vanilla (applicable only if a vanilla shelf exists)
    shelf = (b["n_lost"] is not None and b["n_lost"] >= REGIME_MIN_LOST
             and b["delta"] is not None and b["delta"] > 0)
    d_b, d_c = b["delta"], c["delta"]
    ic_b, ic_c = b["incoherence_D"], c["incoherence_D"]
    halved_delta = d_b is not None and d_c is not None and d_b > 0 and d_c <= 0.5 * d_b
    halved_incoh = ic_b is not None and ic_c is not None and (ic_b == 0 or ic_c <= 0.5 * ic_b)
    p4 = bool(shelf and halved_delta and halved_incoh)
    return {
        "P-R1-1_rlm_ge_naive": dict(rlm_dec_acc=b["decision_acc"], naive_dec_acc=a["decision_acc"],
                                    passed=p1),
        "P-R1-2_freeform_sheds_witness": dict(witness_survival_returns=ws,
                                              n_touched_denied=b["n_touched_D"],
                                              threshold=0.5, min_n=REGIME_MIN_LOST, passed=p2),
        "P-R1-3_delta_readings": dict(delta_naive=a["delta"], delta_vanilla=b["delta"],
                                      delta_cert=c["delta"],
                                      note="both readings preregistered informative (see prereg)"),
        "P-R1-4_cert_halves": dict(applicable_vanilla_shelf=shelf, n_lost_vanilla=b["n_lost"],
                                   delta_vanilla=d_b, delta_cert=d_c, halved_delta=halved_delta,
                                   incoherence_vanilla=ic_b, incoherence_cert=ic_c,
                                   halved_incoherence=halved_incoh, passed=p4),
    }


def do_score():
    items = load_items()
    cache = load_cache()
    models = [m for m in MODELS if any(k[0] == m for k in cache)]
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]
    out = dict(design=dict(n_items=len(items), arms=sorted({it["arm"] for it in items}),
                           conditions=CONDITIONS, root_models=models, naive_words=NAIVE_WORDS,
                           sub_words_budget=SUB_WORDS, max_subcalls=MAX_SUB,
                           candidates_disclosed=True),
               per_model={}, cost_usd={}, total_cost_usd=0.0)
    all_csv = []
    for alias in models:
        rows = score_rows(alias, items, cache)
        for r in rows:
            all_csv.append(dict(model=alias, **r))
        arms = sorted({it["arm"] for it in items})
        pm = {"per_arm": {}, "pooled": {}}
        for scope, subset in [("pooled", rows)] + [(arm, [r for r in rows if r["arm"] == arm]) for arm in arms]:
            block = {cond: _agg([r for r in subset if r["condition"] == cond]) for cond in CONDITIONS}
            if scope == "pooled":
                pm["pooled"] = block
            else:
                pm["per_arm"][scope] = block
        pm["predictions"] = _predictions(pm["pooled"])
        out["per_model"][alias] = pm
    out["cost_usd"] = {m: round(cost_usd(m, tok[m]), 4) for m in models}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)
    if all_csv:
        with open(os.path.join(HERE, "scored.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(all_csv[0].keys()))
            w.writeheader()
            w.writerows(all_csv)
    _print(out, models)


def _print(out, models):
    hdr = (f"{'cond':9} {'decAll':>6} {'decD':>6} {'decA':>6} {'whichD':>7} {'S':>6} {'J':>6} "
           f"{'Δ':>7} {'incoh':>6} {'gap':>6} {'touch':>6} {'retW':>6} {'nSub':>5} {'giveUp':>6}")
    for alias in models:
        pm = out["per_model"][alias]
        print(f"\n=== {alias} (pooled) ===")
        print(hdr)
        for cond in CONDITIONS:
            a = pm["pooled"][cond]
            print(f"{cond:9} {_f(a['decision_acc']):>6} {_f(a['decision_acc_D']):>6} "
                  f"{_f(a['decision_acc_A']):>6} {_f(a['which_acc_D']):>7} {_f(a['S']):>6} "
                  f"{_f(a['J']):>6} {_f(a['delta']):>7} {_f(a['incoherence_D']):>6} "
                  f"{_f(a['named_gap_D']):>6} {_f(a['touched_relevant_D']):>6} "
                  f"{_f(a['ret_words']):>6} {_f(a['n_sub']):>5} {_f(a['gave_up']):>6}")
        for arm, block in pm["per_arm"].items():
            print(f"  -- {arm} --")
            for cond in CONDITIONS:
                a = block[cond]
                print(f"  {cond:9} decD={_f(a['decision_acc_D'])} whichD={_f(a['which_acc_D'])} "
                      f"S={_f(a['S'])} J={_f(a['J'])} Δ={_f(a['delta'])} incoh={_f(a['incoherence_D'])} "
                      f"wsRet={_f(a['witness_survival_returns'])}(n={a['n_touched_D']})")
        for k, v in pm["predictions"].items():
            tag = "PASS" if v.get("passed") else ("    " if "passed" not in v else "FAIL")
            print(f"    {tag}  {k}: {json.dumps({kk: vv for kk, vv in v.items() if kk != 'passed'})}")
    print(f"\ncost/model: {out['cost_usd']}   total: ${out['total_cost_usd']}   wrote {RESULTS}")


def _f(x):
    return "—" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def do_smoke(alias):
    items = load_items()
    smoke = [items[0], items[12], items[24]]  # ledger-A, ledger-D, realdoc
    run_model(alias, smoke)
    cache = load_cache()
    api, state = _cache_api(alias, cache)
    for it in smoke:
        print(f"\n{'='*70}\n{it['id']} arm={it['arm']} truth={it['truth']} "
              f"failing={it['failing_param']!r} code={it['code']} relevant_slice={it['relevant_slice']}")
        print(f"POLICY: {it['policy_text'][:230]}")
        notes = cache.get((alias, it["id"], "naive_compress"), {}).get("text", "")
        nd = cache.get((alias, it["id"], "naive_decision"), {}).get("text", "")
        nw = cache.get((alias, it["id"], "naive_which"), {}).get("text", "")
        pol = [p for p in it["parameters"] if p.get("policy")]
        fail = next((p for p in pol if not p["passes"]), None)
        print(f"\n[naive] ({len(notes.split())}w) {notes.strip()[:300]}")
        print(f"   S(fail in notes)={retained(notes, fail['value']) if fail else None}  "
              f"dec: {nd.strip()[:30]}  which: {nw.strip()[:70]}")
        for cond in ("vanilla", "cert"):
            state["iid"] = it["id"]
            tr = run_rlm(api, it, cond, match_param)
            print(f"\n[{cond}] iters={tr['n_iters']} n_sub={tr['n_sub']} gave_up={tr['gave_up']} "
                  f"-> DECISION={tr['decision']} PARAMETER={tr['parameter']}")
            for sc in tr["subcalls"]:
                surv = (retained(sc["ret"] or "", fail["value"]) if fail else None)
                rel = "REL" if sc["is_relevant"] else "   "
                print(f"   {rel} q[{sc['slice_id']}]({sc['ret_words']}w survW={surv}): "
                      f"{(sc['ret'] or '').strip()[:150]}")


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
