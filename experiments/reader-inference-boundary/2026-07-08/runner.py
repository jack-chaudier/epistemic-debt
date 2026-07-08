#!/usr/bin/env python3
"""Reader-inference-boundary run + scorer. See prereg_reader_inference_boundary.md.

Pure read-channel probe (NO compressor): notes are constructed deterministically per class.

  smoke --model grok        # 3 items (one per derivable class) end-to-end, prints raw
  run   --model grok|haiku|gpt [--cls a|b|c|d] [--limit N]
  score                     # per-class recovery, Wilson CIs, predictions pass/fail

Idempotent cache in responses_raw.jsonl keyed by (model,item,call); hard cap 3000/model.
Stdlib only; temperature 0; cost logged.
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lib"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from runner3 import match_param  # noqa: E402
from dissociation import parse_which, wilson  # noqa: E402  (corrected last-anchor parser + Wilson)
from providers import chat, cost_usd  # noqa: E402

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "reader_inference_boundary_results.json")
MODELS = ["grok", "haiku", "gpt"]
HARD_CAP = 3000
CLASSES = ("a", "b", "c", "d")

PREDICTIONS = {
    "P-RIB-0_retrieval_control": "recovery(d) >= 0.85",
    "P-RIB-1_elimination_works": "recovery(b) >= 0.75",
    "P-RIB-2_arithmetic_fails": "recovery(c) <= 0.50",
    "P-RIB-3_depth_boundary": "recovery(b)-recovery(c) >= 0.25 AND b.ci_lo > c.ci_hi",
    "P-RIB-4_elimination_genuine": "recovery(a) <= 0.50 AND b.ci_lo > a.ci_hi",
    "P-RIB-5_arithmetic_in_capacity": "direct_arith_accuracy >= 0.85",
}

# The WHICH probe discloses the verdict (DENIED) and the candidate set (via policy_text) — the
# deployed setting of I.3. Notes are confound-clean (no verdict/threshold words; selfcheck).
WHICH = (" This case was adjudicated DENIED under the policy above. Exactly one of the policy "
         "parameters has a reading outside its allowed range, and that is what caused the denial. "
         "Name that single parameter. Reply exactly: PARAMETER: <name>.")
ABSTAIN = (" If the notes do not let you determine which parameter it was, reply exactly: "
           "PARAMETER: INSUFFICIENT_EVIDENCE.")


def _arith_question(ap):
    rel = "higher than" if ap["dirword"] == "above" else "lower than"
    word = "at most" if ap["dir"] == "max" else "at least"
    return (f"A reading was {ap['offset']} {ap['unit']} {rel} an earlier baseline of "
            f"{ap['base']} {ap['unit']}. The requirement is that the reading be {word} "
            f"{ap['thr']} {ap['unit']}. Does the reading meet the requirement? "
            f"Reply exactly: RESULT: PASS or RESULT: FAIL.")


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

    def api(call, content):
        key = (alias, iid, call)
        if key in cache:
            return cache[key]["text"]
        if len(cache) - n0 + 1 > HARD_CAP:
            sys.exit(f"HARD CAP {HARD_CAP} reached for {alias}")
        text, usage = chat(alias, [{"role": "user", "content": content}])
        rec = dict(model=alias, item=iid, call=call, text=text, usage=usage)
        with open(RAW, "a") as f:
            f.write(json.dumps(rec) + "\n")
        cache[key] = rec
        return text

    for n, it in enumerate(items):
        iid = it["id"]
        notes = it["policy_text"] + "\n\nCase notes:\n" + it["notes"] + "\n\n"
        api("which", notes + WHICH)
        api("which_abstain", notes + WHICH + ABSTAIN)
        if it["cls"] == "c" and it["arith_probe"]:
            api("arith", _arith_question(it["arith_probe"]))
        if (n + 1) % 40 == 0:
            print(f"  {alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)
    return cache


def _recovery_cell(rows):
    k = sum(1 for r in rows if r["recovered"])
    n = len(rows)
    return dict(k=k, n=n, p=(round(k / n, 4) if n else None), ci=wilson(k, n))


def do_score():
    items = [json.loads(l) for l in open(os.path.join(HERE, "items.jsonl"))]
    cache = load_cache()
    models = sorted({k[0] for k in cache}) or MODELS
    out = {"design": dict(n_per_class=60, classes=list(CLASSES), disclosed_candidates=True,
                          reader="direct (no compressor)", predictions=PREDICTIONS),
           "per_model": {}}
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, _i, _c), r in cache.items():
        tok[m]["prompt"] += r["usage"]["prompt"]
        tok[m]["completion"] += r["usage"]["completion"]

    for alias in models:
        by_cls = {c: [] for c in CLASSES}
        arith_rows = []
        unmatched = defaultdict(int)
        abstain_cells = {c: [] for c in CLASSES}
        for it in items:
            iid = it["id"]
            g = lambda call: cache.get((alias, iid, call), {}).get("text")
            if g("which") is None:
                continue
            wp, _ = parse_which(g("which"), it["parameters"])
            recovered = (wp == it["culprit"])
            if wp in ("UNMATCHED", None):
                unmatched[it["cls"]] += 1
            by_cls[it["cls"]].append(dict(item=iid, which=wp, recovered=recovered))
            ab, _ = parse_which(g("which_abstain"), it["parameters"])
            abstain_cells[it["cls"]].append(ab == "INSUFFICIENT_EVIDENCE")
            if it["cls"] == "c" and it["arith_probe"] and g("arith") is not None:
                txt = (g("arith") or "").upper()
                import re as _re
                mm = _re.search(r"RESULT\s*:?\s*\**\s*(PASS|FAIL)", txt)
                pred = mm.group(1) if mm else None
                arith_rows.append(pred == it["arith_probe"]["truth"])

        cells = {c: _recovery_cell(by_cls[c]) for c in CLASSES}
        da_k = sum(1 for x in arith_rows if x)
        da = dict(k=da_k, n=len(arith_rows),
                  p=(round(da_k / len(arith_rows), 4) if arith_rows else None),
                  ci=wilson(da_k, len(arith_rows)))
        rec = {c: cells[c]["p"] for c in CLASSES}

        def lo(c):
            return cells[c]["ci"][0]

        def hi(c):
            return cells[c]["ci"][1]

        preds = {}
        preds["P-RIB-0_retrieval_control"] = dict(
            value=rec["d"], passed=bool(rec["d"] is not None and rec["d"] >= 0.85))
        preds["P-RIB-1_elimination_works"] = dict(
            value=rec["b"], passed=bool(rec["b"] is not None and rec["b"] >= 0.75))
        preds["P-RIB-2_arithmetic_fails"] = dict(
            value=rec["c"], passed=bool(rec["c"] is not None and rec["c"] <= 0.50))
        preds["P-RIB-3_depth_boundary"] = dict(
            gap=(round(rec["b"] - rec["c"], 4) if rec["b"] is not None and rec["c"] is not None else None),
            ci_separated=bool(lo("b") is not None and hi("c") is not None and lo("b") > hi("c")),
            passed=bool(rec["b"] is not None and rec["c"] is not None
                        and (rec["b"] - rec["c"]) >= 0.25 and lo("b") > hi("c")))
        preds["P-RIB-4_elimination_genuine"] = dict(
            value_a=rec["a"],
            ci_separated=bool(lo("b") is not None and hi("a") is not None and lo("b") > hi("a")),
            passed=bool(rec["a"] is not None and rec["a"] <= 0.50
                        and lo("b") is not None and hi("a") is not None and lo("b") > hi("a")))
        preds["P-RIB-5_arithmetic_in_capacity"] = dict(
            value=da["p"], passed=bool(da["p"] is not None and da["p"] >= 0.85))

        out["per_model"][alias] = dict(
            recovery=cells, direct_arith=da, abstain_rate={c: (round(sum(abstain_cells[c]) / len(abstain_cells[c]), 4)
                                                               if abstain_cells[c] else None) for c in CLASSES},
            unmatched=dict(unmatched), predictions=preds,
            cost_usd=round(cost_usd(alias, tok[alias]), 4))

    # cross-model verdict logic (stated in prereg)
    def all_pass(pkeys):
        return {m: all(out["per_model"][m]["predictions"][k]["passed"] for k in pkeys)
                for m in out["per_model"]}
    boundary_keys = ["P-RIB-0_retrieval_control", "P-RIB-1_elimination_works",
                     "P-RIB-2_arithmetic_fails", "P-RIB-3_depth_boundary",
                     "P-RIB-5_arithmetic_in_capacity"]
    per_model_boundary = all_pass(boundary_keys)
    refuted = {m: (out["per_model"][m]["predictions"]["P-RIB-2_arithmetic_fails"]["passed"] is False
                   and out["per_model"][m]["predictions"]["P-RIB-5_arithmetic_in_capacity"]["passed"])
               for m in out["per_model"]}
    out["verdict"] = dict(
        per_model_boundary_confirmed=per_model_boundary,
        boundary_is_cross_model_constant=bool(per_model_boundary and all(per_model_boundary.values())),
        retrieval_reading_refuted_on=[m for m, v in refuted.items() if v])
    out["cost_usd"] = {m: out["per_model"][m]["cost_usd"] for m in out["per_model"]}
    out["total_cost_usd"] = round(sum(out["cost_usd"].values()), 4)
    json.dump(out, open(RESULTS, "w"), indent=1)

    for alias in models:
        pm = out["per_model"][alias]
        print(f"\n=== {alias} === (cost ${pm['cost_usd']})")
        for c in CLASSES:
            cell = pm["recovery"][c]
            print(f"  class {c}: recovery {cell['p']} {cell['ci']} (n={cell['n']}) "
                  f"abstain={pm['abstain_rate'][c]} unmatched={pm['unmatched'].get(c, 0)}")
        print(f"  direct_arith: {pm['direct_arith']['p']} {pm['direct_arith']['ci']} "
              f"(n={pm['direct_arith']['n']})")
        for k, v in pm["predictions"].items():
            print(f"    {'PASS' if v['passed'] else 'FAIL'}  {k}: {PREDICTIONS[k]}")
    print(f"\nverdict: {json.dumps(out['verdict'])}")
    print(f"total cost: ${out['total_cost_usd']}")
    print(f"wrote {RESULTS}")


def do_score_c2():
    items = [json.loads(l) for l in open(os.path.join(HERE, "items_c2.jsonl"))]
    cache = load_cache()
    models = sorted({k[0] for k in cache if k[1].startswith("rib-c2-")}) or MODELS
    out = {"design": dict(n=len(items), disclosed_candidates=True,
                          note="base-only leak forced to chance; see prereg_c2_confirmatory.md"),
           "per_model": {}}
    # base-only heuristic recovery on the corpus (P-C2-3, mechanical)
    base_leak_k = 0
    for it in items:
        cs = it["culprit_slot"]
        am = {int(k): v for k, v in it["arith"].items()}
        pol = it["parameters"]
        k_oth = [k for k in am if k != cs][0]

        def bf(k):
            p = pol[k]
            b = am[k]["base"]
            return (b > p["thr"]) if p["dir"] == "max" else (b < p["thr"])
        if bf(cs) and not bf(k_oth):
            base_leak_k += 1
    out["base_only_leak"] = round(base_leak_k / len(items), 4)
    out["P-C2-3_no_residual_base_leak"] = dict(value=out["base_only_leak"],
                                               passed=bool(out["base_only_leak"] <= 0.34))
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    for (m, i, _c), r in cache.items():
        if i.startswith("rib-c2-"):
            tok[m]["prompt"] += r["usage"]["prompt"]
            tok[m]["completion"] += r["usage"]["completion"]
    passes_1 = passes_2 = 0
    for alias in models:
        rows = []
        unmatched = 0
        for it in items:
            rec = cache.get((alias, it["id"], "which"))
            if rec is None:
                continue
            wp, _ = parse_which(rec["text"], it["parameters"])
            if wp in ("UNMATCHED", None):
                unmatched += 1
            rows.append(dict(recovered=(wp == it["culprit"])))
        cell = _recovery_cell(rows)
        p1 = bool(cell["p"] is not None and cell["p"] >= 0.60)
        p2 = bool(cell["ci"][0] is not None and cell["ci"][0] > 0.50)
        passes_1 += int(p1)
        passes_2 += int(p2)
        out["per_model"][alias] = dict(recovery=cell, unmatched=unmatched,
                                       P_C2_1=p1, P_C2_2=p2,
                                       cost_usd=round(cost_usd(alias, tok[alias]), 4))
    out["P-C2-1_recovery_survives"] = dict(models_passing=passes_1, criterion=">=2 of 3",
                                           passed=bool(passes_1 >= 2))
    out["P-C2-2_above_guess_floor"] = dict(models_passing=passes_2, criterion=">=2 of 3",
                                           passed=bool(passes_2 >= 2))
    out["verdict_retrieval_only_refuted"] = bool(
        out["P-C2-1_recovery_survives"]["passed"] and out["P-C2-2_above_guess_floor"]["passed"]
        and out["P-C2-3_no_residual_base_leak"]["passed"])
    out["total_cost_usd"] = round(sum(v["cost_usd"] for v in out["per_model"].values()), 4)
    json.dump(out, open(os.path.join(HERE, "reader_inference_boundary_c2_results.json"), "w"), indent=1)
    for alias in models:
        pm = out["per_model"][alias]
        print(f"{alias}: recovery {pm['recovery']['p']} {pm['recovery']['ci']} (n={pm['recovery']['n']}) "
              f"unmatched={pm['unmatched']} P-C2-1={pm['P_C2_1']} P-C2-2={pm['P_C2_2']}")
    print(f"base-only leak (P-C2-3): {out['base_only_leak']} -> {'PASS' if out['P-C2-3_no_residual_base_leak']['passed'] else 'FAIL'}")
    print(f"P-C2-1 (>=2/3 recovery>=0.60): {'PASS' if out['P-C2-1_recovery_survives']['passed'] else 'FAIL'} ({passes_1}/3)")
    print(f"P-C2-2 (>=2/3 ci_lo>0.50): {'PASS' if out['P-C2-2_above_guess_floor']['passed'] else 'FAIL'} ({passes_2}/3)")
    print(f"VERDICT retrieval-only refuted at prereg strength: {out['verdict_retrieval_only_refuted']}")
    print(f"total c2 cost: ${out['total_cost_usd']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score", "run-c2", "score-c2"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--cls", choices=CLASSES)
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    if a.cmd == "score-c2":
        do_score_c2()
        return
    if a.cmd == "run-c2":
        items = [json.loads(l) for l in open(os.path.join(HERE, "items_c2.jsonl"))]
        if a.limit:
            items = items[:a.limit]
        run_model(a.model, items)
        print(f"{a.model} c2 done ({len(items)} items)")
        return
    items = [json.loads(l) for l in open(os.path.join(HERE, "items.jsonl"))]
    if a.cls:
        items = [it for it in items if it["cls"] == a.cls]
    if a.cmd == "smoke":
        # one item per derivable class (b, c, d) + one underivable (a)
        picks, seen = [], set()
        for it in items:
            if it["cls"] not in seen:
                picks.append(it)
                seen.add(it["cls"])
        run_model(a.model, picks)
        cache = load_cache()
        for it in picks:
            print(f"\n--- {it['id']} cls={it['cls']} culprit={it['culprit']!r}")
            print("  NOTES:", it["notes"].replace("\n", " | "))
            for call in ("which", "which_abstain", "arith"):
                r = cache.get((a.model, it["id"], call))
                if r:
                    print(f"  [{call}] {r['text'].strip()[:200]}")
        return
    if a.limit:
        items = items[:a.limit]
    run_model(a.model, items)
    print(f"{a.model} done ({len(items)} items)")


if __name__ == "__main__":
    main()
