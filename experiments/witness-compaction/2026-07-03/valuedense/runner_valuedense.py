#!/usr/bin/env python3
"""Phase A: contract-blind witness-aware compaction (valuedense + auditor arms)
vs the v5 plain-15 baseline. See prereg_valuedense.md (fixed before any call)."""
import argparse, csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03")
V5 = os.path.join(MULTI, "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, MULTI)
from runner3 import (ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD,
                     NUM_RE)
from providers import chat, cost_usd

ITEMS = os.path.join(V5, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "valuedense_results.json")
HARD_CAP = 1500
WL = 15
ALIASES = ["grok", "haiku"]

PLAIN_SYS = (f"You are a context compaction engine for an operations assistant. Compress the "
             f"following incident file to at most {WL} words. A future analyst will need to "
             f"answer questions about this incident, but you do not know which questions. "
             f"Output only the compressed notes.")
VALUEDENSE_SYS = (f"You are a context compaction engine for an operations assistant. Compress the "
                  f"following incident file to at most {WL} words — a hard limit (a reading like "
                  f"'wind 11.1 m/s' counts as 3 words). A future analyst will need to answer "
                  f"questions about this incident, but you do not know which questions. Spend the "
                  f"budget on concrete parameter readings (name, number, unit) rather than prose, "
                  f"keeping the readings most likely to decide any pass/fail or threshold "
                  f"question; if they do not all fit, keep only the most decision-relevant few. "
                  f"Output only the compressed notes.")
AUDITOR_LIST = ("You are preparing a contract-blind audit digest. List the 6 facts from the "
                "following incident file that a future auditor would most need, one per line, "
                "each with its exact figure if it has one. You do not know what the auditor "
                "will ask. Output only the list.")
AUDITOR_SYS = (f"You are a context compaction engine for an operations assistant. Compress the "
               f"incident file below to at most {WL} words — a hard limit — using the audit list "
               f"to choose what to keep. A future analyst will need to answer questions about "
               f"this incident, but you do not know which questions. Output only the compressed "
               f"notes.")


def load_baseline(alias):
    """Plain-15 summaries + probes from the cached v5 run."""
    base = {}
    for line in open(os.path.join(V5, "responses_raw.jsonl")):
        r = json.loads(line)
        if r["model"] == alias:
            base[(r["item"], r["call"])] = r["text"]
    return base


def load_plain25(alias):
    """Realized-length-matched control: manifest-phase plain25 summaries + probes."""
    base = {}
    for line in open(os.path.join(MULTI, "manifest", "responses_raw.jsonl")):
        r = json.loads(line)
        if r["model"] == alias and r["arm"] == "plain25":
            base[(r["item"], r["call"])] = r["text"]
    return base


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
        sys.exit("HARD CAP")
    text, usage = chat(alias, messages)
    rec = dict(model=key_fn[0], arm=key_fn[1], item=key_fn[2], call=key_fn[3],
               text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(alias, items, arms, end):
    cache = load_cache()
    for it in items[:end]:
        iid = it["id"]
        for arm in arms:
            if arm == "valuedense":
                summary = api(alias, [{"role": "system", "content": VALUEDENSE_SYS},
                                      {"role": "user", "content": it["document"]}],
                              cache, (alias, arm, iid, "compress"))
            else:  # auditor: two-pass
                lst = api(alias, [{"role": "system", "content": AUDITOR_LIST},
                                  {"role": "user", "content": it["document"]}],
                          cache, (alias, arm, iid, "auditlist"))
                summary = api(alias, [{"role": "system", "content": AUDITOR_SYS},
                                      {"role": "user", "content":
                                       "AUDIT LIST:\n" + lst + "\n\nINCIDENT FILE:\n"
                                       + it["document"]}],
                              cache, (alias, arm, iid, "compress"))
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(alias, [{"role": "user", "content": notes + ANS_SUFFIX}],
                cache, (alias, arm, iid, "decision"))
            api(alias, [{"role": "user", "content": notes + WHICH_SUFFIX}],
                cache, (alias, arm, iid, "which"))
            api(alias, [{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
                cache, (alias, arm, iid, "which_abstain"))
        print(f"{alias} {iid} done ({len(cache)})", flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def row_from(alias, arm, it, summary, dtxt, wtxt, watxt):
    pol = [p for p in it["parameters"] if p["policy"]]
    fail = next((p for p in pol if not p["passes"]), None)
    m = ANS_RE.search(dtxt or "")
    dec = m.group(1).upper() if m else None
    wp, _ = parse_which(wtxt, it["parameters"])
    wa, _ = parse_which(watxt, it["parameters"])
    target = it["failing_param"] or "NONE"
    return dict(
        model=alias, arm=arm, item=it["id"], truth=it["truth"],
        summary_words=len(summary.split()),
        n_values=len(NUM_RE.findall(summary)),
        ret_policy=sum(retained(summary, p["value"]) for p in pol) / 3,
        fail_retained=retained(summary, fail["value"]) if fail else None,
        decision_correct=dec == it["truth"],
        which=wp, which_correct=wp == target,
        abstained=wa == "INSUFFICIENT_EVIDENCE")


def score(items):
    cache = load_cache()
    rows = []
    for alias in ALIASES:
        base = load_baseline(alias)
        p25 = load_plain25(alias)
        for it in items:
            iid = it["id"]
            if (iid, "compress") in base:
                rows.append(row_from(alias, "plain_v5", it, base[(iid, "compress")],
                                     base.get((iid, "decision")), base.get((iid, "which")),
                                     base.get((iid, "which_abstain"))))
            if (iid, "compress") in p25:
                rows.append(row_from(alias, "plain25", it, p25[(iid, "compress")],
                                     p25.get((iid, "decision")), p25.get((iid, "which")),
                                     p25.get((iid, "which_abstain"))))
            for arm in ("valuedense", "auditor"):
                r = cache.get((alias, arm, iid, "compress"))
                if r is None:
                    continue
                g = lambda call: cache.get((alias, arm, iid, call), {}).get("text")
                rows.append(row_from(alias, arm, it, r["text"], g("decision"),
                                     g("which"), g("which_abstain")))
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    frac = lambda k, n: k / n if n else float("nan")
    report, preds = {}, {}
    for alias in ALIASES:
        report[alias] = {}
        stats = {}
        for arm in ("plain_v5", "plain25", "valuedense", "auditor"):
            sub = [r for r in rows if r["model"] == alias and r["arm"] == arm]
            if not sub:
                continue
            den = [r for r in sub if r["truth"] == "DENIED"]
            lost = [r for r in den if not r["fail_retained"]]
            kept = [r for r in den if r["fail_retained"]]
            stats[arm] = dict(
                n=len(sub), mean_words=sum(r["summary_words"] for r in sub) / len(sub),
                mean_values=sum(r["n_values"] for r in sub) / len(sub),
                retention=sum(r["ret_policy"] for r in sub) / len(sub),
                n_lost=len(lost), n_retained=len(kept),
                which_denied_overall=dict(
                    k=sum(r["which_correct"] for r in den), n=len(den),
                    p=frac(sum(r["which_correct"] for r in den), len(den)),
                    ci95=wilson(sum(r["which_correct"] for r in den), len(den))),
                which_lost=frac(sum(r["which_correct"] for r in lost), len(lost)),
                which_retained=frac(sum(r["which_correct"] for r in kept), len(kept)),
                decision_overall=frac(sum(r["decision_correct"] for r in sub), len(sub)),
                abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
                abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)))
        report[alias] = stats
        # realized-length-matched controls (prereg amendment): valuedense vs
        # manifest plain25; auditor vs v5 plain15
        for arm, ctrl in (("valuedense", "plain25"), ("auditor", "plain_v5")):
            if arm not in stats or ctrl not in stats:
                continue
            b, a = stats[ctrl], stats[arm]
            applicable = a["n_lost"] >= 8 and a["n_retained"] >= 8
            preds[f"{alias}:{arm}"] = dict(
                applicable_A4=applicable,
                A1_retention=dict(base=b["retention"], arm=a["retention"],
                                  passed=bool(a["retention"] >= b["retention"] + 0.15)),
                A2_justified=dict(base=b["which_denied_overall"]["p"],
                                  arm=a["which_denied_overall"]["p"],
                                  passed=bool(a["which_denied_overall"]["p"]
                                              >= b["which_denied_overall"]["p"] + 0.15)),
                A3_blind_price=dict(arm=a["retention"],
                                    passed=bool(a["retention"] <= 0.80)),
                A4_shelf_persists=dict(which_lost=a["which_lost"],
                                       which_retained=a["which_retained"],
                                       passed=bool(a["which_lost"] <= 1 / 3
                                                   and a["which_retained"] >= 0.7)
                                       if applicable else None))
    tok = {}
    for r in cache.values():
        t = tok.setdefault(r["model"], dict(prompt=0, completion=0))
        t["prompt"] += r["usage"]["prompt"]
        t["completion"] += r["usage"]["completion"]
    cost = {a: round(cost_usd(a, tok[a]), 4) for a in tok}
    for alias in ALIASES:
        print(f"\n===== {alias} =====")
        for arm, st in report[alias].items():
            print(f"  {arm:11s}: words={st['mean_words']:.1f} values={st['mean_values']:.1f} "
                  f"retention={st['retention']:.3f} lost/ret={st['n_lost']}/{st['n_retained']} "
                  f"WHICH-denied={st['which_denied_overall']['k']}/{st['which_denied_overall']['n']} "
                  f"(lost={st['which_lost']:.2f} ret={st['which_retained']:.2f}) "
                  f"dec={st['decision_overall']:.2f}")
    print()
    for key, p in preds.items():
        marks = " ".join(f"{k.split('_')[0]}={'PASS' if v['passed'] else 'FAIL' if v['passed'] is not None else 'n/a'}"
                         for k, v in p.items() if k.startswith("A"))
        print(f"  {key:18s} {marks}")
    print(f"cost: {cost} total=${sum(cost.values()):.3f}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(arms=["valuedense", "auditor"], baseline="v5 plain-15 cached",
                                   models=ALIASES, wl=WL, prereg="prereg_valuedense.md"),
                       per_model=report, preds=preds, tokens=tok, cost_usd=cost,
                       total_cost_usd=round(sum(cost.values()), 4)), f, indent=2)
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    ap.add_argument("--model", choices=ALIASES, default=None)
    ap.add_argument("--arm", choices=["valuedense", "auditor"], default=None)
    ap.add_argument("--end", type=int, default=60)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(ITEMS)]
    if a.cmd == "run":
        arms = [a.arm] if a.arm else ["valuedense", "auditor"]
        for alias in ([a.model] if a.model else ALIASES):
            run(alias, items, arms, a.end)
    else:
        score(items)


if __name__ == "__main__":
    main()
