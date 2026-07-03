#!/usr/bin/env python3
"""Phase D: abstention-routed re-expansion, grok, 30 DENIED v5 items.
Router signal = cached v5 WHICH-ABSTAIN; second pass = WHICH over full document.
See prereg_routing.md (fixed before any call)."""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03")
V5 = os.path.join(MULTI, "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, MULTI)
from runner3 import retained, parse_which, WHICH_SUFFIX
from providers import chat, cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "routing_results.json")
HARD_CAP = 100
ALIAS = "grok"


def load_items():
    return [it for it in map(json.loads, open(os.path.join(V5, "items.jsonl")))
            if it["truth"] == "DENIED"]


def load_v5(alias="grok"):
    out = {}
    for line in open(os.path.join(V5, "responses_raw.jsonl")):
        r = json.loads(line)
        if r["model"] == alias:
            out[(r["item"], r["call"])] = r
    return out


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["item"], r["call"])] = r
    return cache


def api(messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(ALIAS, messages)
    rec = dict(item=key_fn[0], call=key_fn[1], text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(items):
    v5 = load_v5()
    cache = load_cache()
    for it in items:
        iid = it["id"]
        full = it["policy_text"] + "\n\nIncident file:\n" + it["document"] + "\n\n" + WHICH_SUFFIX
        api([{"role": "user", "content": full}], cache, (iid, "which_full"))
        wa, _ = parse_which(v5[(iid, "which_abstain")]["text"], it["parameters"])
        if wa == "INSUFFICIENT_EVIDENCE":
            api([{"role": "user", "content": full}], cache, (iid, "which_routed"))
        print(f"{iid} done ({len(cache)})", flush=True)


def score(items):
    v5 = load_v5()
    cache = load_cache()
    frac = lambda k, n: k / n if n else float("nan")
    rows = []
    for it in items:
        iid = it["id"]
        target = it["failing_param"]
        pol = [p for p in it["parameters"] if p["policy"]]
        fail = next(p for p in pol if not p["passes"])
        notes = v5[(iid, "compress")]["text"]
        wa, _ = parse_which(v5[(iid, "which_abstain")]["text"], it["parameters"])
        abstained = wa == "INSUFFICIENT_EVIDENCE"
        wf, _ = parse_which(cache[(iid, "which_full")]["text"], it["parameters"])
        routed_ans = None
        if abstained:
            wr, _ = parse_which(cache[(iid, "which_routed")]["text"], it["parameters"])
            routed_ans = wr
            pipeline = wr
        else:
            pipeline = wa
        rows.append(dict(
            item=iid, fail_retained=retained(notes, fail["value"]),
            abstained=abstained,
            notes_answer=wa, notes_correct=wa == target,
            full_correct=wf == target,
            routed_correct=(routed_ans == target) if abstained else None,
            pipeline_correct=pipeline == target))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    routed = [r for r in rows if r["abstained"]]
    kept_conf = [r for r in rows if not r["abstained"]]
    full_acc = frac(sum(r["full_correct"] for r in rows), len(rows))
    pipe_acc = frac(sum(r["pipeline_correct"] for r in rows), len(rows))
    routed_acc = frac(sum(r["routed_correct"] for r in routed), len(routed))
    # token accounting
    v5_tok = {"prompt": 0, "completion": 0}
    for it in items:
        r = v5[(it["id"], "which_abstain")]
        v5_tok["prompt"] += r["usage"]["prompt"]
        v5_tok["completion"] += r["usage"]["completion"]
    routed_tok = {"prompt": 0, "completion": 0}
    full_tok = {"prompt": 0, "completion": 0}
    for (iid, call), r in cache.items():
        t = full_tok if call == "which_full" else routed_tok
        t["prompt"] += r["usage"]["prompt"]
        t["completion"] += r["usage"]["completion"]
    pipeline_total = sum(v5_tok.values()) + sum(routed_tok.values())
    full_total = sum(full_tok.values())
    ratio = pipeline_total / full_total
    preds = {
        "P-D1_reexpansion_restores": dict(routed_acc=routed_acc, n_routed=len(routed),
                                          passed=bool(routed_acc >= 0.85)),
        "P-D2_end_to_end": dict(pipeline=pipe_acc, always_full=full_acc,
                                passed=bool(pipe_acc >= 0.85 and pipe_acc >= full_acc - 0.10)),
        "P-D3_cheaper": dict(pipeline_tokens=pipeline_total, full_tokens=full_total,
                             ratio=round(ratio, 3), passed=bool(ratio <= 0.75)),
    }
    false_conf = [r for r in kept_conf if not r["pipeline_correct"]]
    lost = [r for r in rows if not r["fail_retained"]]
    router = dict(precision=frac(sum(1 for r in routed if not r["fail_retained"]), len(routed)),
                  recall=frac(sum(1 for r in lost if r["abstained"]), len(lost)))
    tok = dict(prompt=full_tok["prompt"] + routed_tok["prompt"],
               completion=full_tok["completion"] + routed_tok["completion"])
    cost = round(cost_usd(ALIAS, tok), 4)
    print(f"routed={len(routed)}/30 routed_acc={routed_acc:.3f} pipeline={pipe_acc:.3f} "
          f"always_full={full_acc:.3f} notes_only={frac(sum(r['notes_correct'] for r in rows), len(rows)):.3f}")
    print(f"token ratio={ratio:.3f} ({pipeline_total} vs {full_total}); "
          f"router precision={router['precision']:.2f} recall={router['recall']:.2f}; "
          f"false-confident wrong={len(false_conf)}")
    for k, v in preds.items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")
    print(f"cost: ${cost}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(model=ALIAS, router="cached v5 WHICH-ABSTAIN",
                                   prereg="prereg_routing.md"),
                       notes_only_acc=frac(sum(r["notes_correct"] for r in rows), len(rows)),
                       always_full_acc=full_acc, pipeline_acc=pipe_acc, routed_acc=routed_acc,
                       n_routed=len(routed), token_ratio=round(ratio, 3),
                       router=router, false_confident_wrong=len(false_conf),
                       preds=preds, tokens=tok, cost_usd=cost), f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    items = load_items()
    (run if sys.argv[1] == "run" else score)(items)
