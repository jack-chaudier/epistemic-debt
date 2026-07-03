#!/usr/bin/env python3
"""Loss-manifest intervention: plain-25-word vs 15-word-notes + 10-word OMITTED manifest,
both contract-blind, on the v5 corpus. See prereg_manifest.md (fixed before any call)."""
import argparse, csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, "..", "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner3 import (ANS_RE, CHANGE_RE, retained, match_param, parse_which,
                     ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD, REPAIR_SUFFIX)
from providers import MODELS, chat, cost_usd

ITEMS = os.path.join(V5, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "manifest_results.json")
HARD_CAP = 3000

PLAIN_SYS = ("You are a context compaction engine for an operations assistant. Compress the "
             "following incident file to at most 25 words. A future analyst will need to "
             "answer questions about this incident, but you do not know which questions. "
             "Output only the compressed notes.")
MANIFEST_SYS = ("You are a context compaction engine for an operations assistant. Compress the "
                "following incident file to at most 15 words. A future analyst will need to "
                "answer questions about this incident, but you do not know which questions. "
                "After the notes, add exactly one line beginning 'OMITTED: ' (at most 10 words) "
                "stating what kinds of information you had to drop. "
                "Output only the compressed notes and the OMITTED line.")
ARMS = {"plain25": PLAIN_SYS, "manifest": MANIFEST_SYS}


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["model"], r["arm"], r["item"], r["call"])] = r
    return cache


def api(alias, messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        print("HARD BUDGET CAP REACHED — aborting.")
        sys.exit(2)
    text, usage = chat(alias, messages)
    rec = dict(model=key_fn[0], arm=key_fn[1], item=key_fn[2], call=key_fn[3],
               text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(alias, items, arms):
    cache = load_cache()
    for arm in arms:
        for it in items:
            iid = it["id"]
            summary = api(alias, [{"role": "system", "content": ARMS[arm]},
                                  {"role": "user", "content": it["document"]}],
                          cache, (alias, arm, iid, "compress"))
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(alias, [{"role": "user", "content": notes + ANS_SUFFIX}],
                cache, (alias, arm, iid, "decision"))
            api(alias, [{"role": "user", "content": notes + WHICH_SUFFIX}],
                cache, (alias, arm, iid, "which"))
            api(alias, [{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
                cache, (alias, arm, iid, "which_abstain"))
            api(alias, [{"role": "user", "content": notes + REPAIR_SUFFIX}],
                cache, (alias, arm, iid, "repair"))
        print(f"{alias} arm={arm} done ({len(cache)} cached)", flush=True)


def score(items, aliases):
    cache = load_cache()
    tok = {a: dict(prompt=0, completion=0) for a in aliases}
    for r in cache.values():
        if r["model"] in tok:
            tok[r["model"]]["prompt"] += r["usage"]["prompt"]
            tok[r["model"]]["completion"] += r["usage"]["completion"]
    rows = []
    for alias in aliases:
        for arm in ARMS:
            for it in items:
                iid = it["id"]
                g = lambda call: cache.get((alias, arm, iid, call), {}).get("text")
                summary = g("compress")
                if summary is None:
                    continue
                pol = [p for p in it["parameters"] if p["policy"]]
                fail = next((p for p in pol if not p["passes"]), None)
                m = ANS_RE.search(g("decision") or "")
                dec = m.group(1).upper() if m else None
                wparsed, _ = parse_which(g("which"), it["parameters"])
                waparsed, _ = parse_which(g("which_abstain"), it["parameters"])
                target = it["failing_param"] or "NONE"
                rtxt = g("repair")
                mm = CHANGE_RE.search(rtxt or "")
                repair_specific = bool(mm)
                repair_ok = False
                if mm:
                    pname = match_param(mm.group(1), it["parameters"])
                    val = float(mm.group(2))
                    p = next((p for p in pol if p["name"] == pname), None)
                    if p is not None:
                        crosses = (val <= p["thr"]) if p["dir"] == "max" else (val >= p["thr"])
                        repair_ok = ((pname == target) and crosses) if it["truth"] == "DENIED" \
                            else (not crosses)
                has_manifest = "OMITTED" in summary.upper()
                rows.append(dict(
                    model=alias, arm=arm, item=iid, truth=it["truth"],
                    summary_words=len(summary.split()), has_manifest=has_manifest,
                    fail_retained=retained(summary, fail["value"]) if fail else None,
                    decision=dec, decision_correct=dec == it["truth"],
                    which=wparsed, which_correct=wparsed == target,
                    abstained=waparsed == "INSUFFICIENT_EVIDENCE",
                    incoherent=dec == "DENIED" and wparsed == "NONE",
                    repair_specific=repair_specific, repair_ok=repair_ok))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    frac = lambda k, n: k / n if n else float("nan")
    report, preds = {}, {}
    for alias in aliases:
        arm_stats = {}
        for arm in ARMS:
            sub = [r for r in rows if r["model"] == alias and r["arm"] == arm]
            if not sub:
                continue
            den = [r for r in sub if r["truth"] == "DENIED"]
            lost = [r for r in den if not r["fail_retained"]]
            kept = [r for r in den if r["fail_retained"]]
            arm_stats[arm] = dict(
                n=len(sub), n_lost=len(lost), n_retained=len(kept),
                mean_words=sum(r["summary_words"] for r in sub) / len(sub),
                manifest_rate=frac(sum(r["has_manifest"] for r in sub), len(sub)),
                decision_overall=frac(sum(r["decision_correct"] for r in sub), len(sub)),
                decision_lost=frac(sum(r["decision_correct"] for r in lost), len(lost)),
                which_lost=frac(sum(r["which_correct"] for r in lost), len(lost)),
                which_retained=frac(sum(r["which_correct"] for r in kept), len(kept)),
                abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
                abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)),
                incoherent_lost=frac(sum(r["incoherent"] for r in lost), len(lost)),
                repair_specific_lost=frac(sum(r["repair_specific"] for r in lost), len(lost)),
                repair_ok_lost=frac(sum(r["repair_ok"] for r in lost), len(lost)),
            )
        if len(arm_stats) < 2:
            continue
        pa, ma = arm_stats["plain25"], arm_stats["manifest"]
        applicable = pa["n_lost"] >= 8 and ma["n_lost"] >= 8
        preds[alias] = dict(
            applicable=applicable,
            PM1_fabrication_drops=dict(
                criteria="repair_specific_lost(manifest) <= repair_specific_lost(plain25) - 0.30",
                values=dict(plain25=pa["repair_specific_lost"],
                            manifest=ma["repair_specific_lost"]),
                passed=bool(ma["repair_specific_lost"] <= pa["repair_specific_lost"] - 0.30)),
            PM2_verdict_free=dict(
                criteria="decision_overall(manifest) >= decision_overall(plain25) - 0.10",
                values=dict(plain25=pa["decision_overall"], manifest=ma["decision_overall"]),
                passed=bool(ma["decision_overall"] >= pa["decision_overall"] - 0.10)),
        )
        report[alias] = arm_stats
        print(f"\n===== {alias} =====")
        for arm, st in arm_stats.items():
            print(f"  {arm}: words={st['mean_words']:.1f} lost/ret={st['n_lost']}/{st['n_retained']} "
                  f"manifest_rate={st['manifest_rate']:.2f}")
            for k in ("decision_overall", "decision_lost", "which_lost", "which_retained",
                      "abstain_lost", "incoherent_lost", "repair_specific_lost", "repair_ok_lost"):
                print(f"      {k:22s}: {st[k]:.3f}")
        for name in ("PM1_fabrication_drops", "PM2_verdict_free"):
            p = preds[alias][name]
            print(f"  {name}: {'PASS' if p['passed'] else 'FAIL'}"
                  + ("" if applicable else " (NOT APPLICABLE)") + f"  {p['values']}")
    cost = {a: round(cost_usd(a, tok[a]), 4) for a in aliases}
    print(f"\nmanifest-phase cost: {cost} total=${sum(cost.values()):.3f}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(arms=list(ARMS), corpus="v5 items.jsonl",
                                   prereg="prereg_manifest.md"),
                       per_model=report, preregistered=preds, tokens=tok,
                       cost_usd=cost, total_cost_usd=round(sum(cost.values()), 4)),
                  f, indent=2)
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    ap.add_argument("--model", choices=list(MODELS), default=None)
    ap.add_argument("--arm", choices=list(ARMS), default=None)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(ITEMS)]
    aliases = [a.model] if a.model else list(MODELS)
    if a.cmd == "run":
        for alias in aliases:
            run(alias, items, [a.arm] if a.arm else list(ARMS))
    else:
        score(items, list(MODELS))


if __name__ == "__main__":
    main()
