#!/usr/bin/env python3
"""Cross-model debt transfer: 4 compressors x 4 answerers on the v5 corpus.
Off-diagonal cells probe each answerer with each *other* compressor's cached v5
summary (DECISION, WHICH, WHICH-ABSTAIN). Diagonal reuses v5. See prereg_transfer.md."""
import argparse, csv, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, "..", "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner3 import (ANS_RE, GIST_RE, retained, parse_which,
                     ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD)
from providers import MODELS, chat, cost_usd

ITEMS = os.path.join(V5, "items.jsonl")
V5_RAW = os.path.join(V5, "responses_raw.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "transfer_results.json")
HARD_CAP = 3000
ALIASES = list(MODELS)


def load_v5():
    cache = {}
    with open(V5_RAW) as f:
        for line in f:
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["compressor"], r["answerer"], r["item"], r["call"])] = r
    return cache


def api(answerer, messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        print("HARD BUDGET CAP REACHED — aborting.")
        sys.exit(2)
    text, usage = chat(answerer, messages)
    rec = dict(compressor=key_fn[0], answerer=key_fn[1], item=key_fn[2], call=key_fn[3],
               text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(answerer, items):
    v5 = load_v5()
    cache = load_cache()
    for comp in ALIASES:
        if comp == answerer:
            continue
        for it in items:
            iid = it["id"]
            srec = v5.get((comp, iid, "compress"))
            if srec is None:
                print(f"missing v5 summary {comp} {iid}; skipping")
                continue
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + srec["text"] + "\n\n"
            api(answerer, [{"role": "user", "content": notes + ANS_SUFFIX}],
                cache, (comp, answerer, iid, "decision"))
            api(answerer, [{"role": "user", "content": notes + WHICH_SUFFIX}],
                cache, (comp, answerer, iid, "which"))
            api(answerer, [{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
                cache, (comp, answerer, iid, "which_abstain"))
        print(f"answerer={answerer} compressor={comp} done ({len(cache)} cached)", flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def get_probe(v5, cache, comp, ans, iid, call):
    if comp == ans:
        r = v5.get((comp, iid, call))
    else:
        r = cache.get((comp, ans, iid, call))
    return r["text"] if r else None


def score(items):
    global ALIASES
    v5 = load_v5()
    cache = load_cache()
    # exclude arms without a (near-)complete set of v5 summaries (e.g. gemini:
    # free-tier key capped at 20 req/day — see v5/prereg.md amendment 2)
    ALIASES = [a for a in ALIASES
               if sum(1 for it in items if (a, it["id"], "compress") in v5) >= 50]
    print(f"scoring grid over: {ALIASES}")
    tok = {a: dict(prompt=0, completion=0) for a in ALIASES}
    for r in cache.values():
        tok[r["answerer"]]["prompt"] += r["usage"]["prompt"]
        tok[r["answerer"]]["completion"] += r["usage"]["completion"]
    rows = []
    for comp in ALIASES:
        for it in items:
            iid = it["id"]
            srec = v5.get((comp, iid, "compress"))
            if srec is None:
                continue
            summary = srec["text"]
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            fail_ret = retained(summary, fail["value"]) if fail else None
            any_lost = not all(retained(summary, p["value"]) for p in pol)
            for ans in ALIASES:
                d = get_probe(v5, cache, comp, ans, iid, "decision")
                w = get_probe(v5, cache, comp, ans, iid, "which")
                wa = get_probe(v5, cache, comp, ans, iid, "which_abstain")
                if d is None:
                    continue
                m = ANS_RE.search(d or "")
                dec = m.group(1).upper() if m else None
                wparsed, _ = parse_which(w, it["parameters"])
                waparsed, _ = parse_which(wa, it["parameters"])
                target = it["failing_param"] or "NONE"
                rows.append(dict(
                    compressor=comp, answerer=ans, item=iid, truth=it["truth"],
                    fail_retained=fail_ret, any_policy_lost=any_lost,
                    decision=dec, decision_correct=dec == it["truth"],
                    which=wparsed, which_correct=wparsed == target,
                    which_confab=(wparsed not in (None, "NONE", "INSUFFICIENT_EVIDENCE",
                                                  "UNMATCHED") and wparsed != target),
                    abstained=waparsed == "INSUFFICIENT_EVIDENCE",
                    incoherent=dec == "DENIED" and wparsed == "NONE"))
    with open(SCORED, "w", newline="") as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)

    frac = lambda k, n: k / n if n else float("nan")
    pair_stats, comp_applicable = {}, {}
    for comp in ALIASES:
        den = [r for r in rows if r["compressor"] == comp and r["answerer"] == comp
               and r["truth"] == "DENIED"]
        # cell sizes are compressor properties; compute from any answerer's rows
        den_any = [r for r in rows if r["compressor"] == comp and r["truth"] == "DENIED"
                   and r["answerer"] == ALIASES[0]]
        n_lost = sum(1 for r in den_any if not r["fail_retained"])
        n_kept = sum(1 for r in den_any if r["fail_retained"])
        comp_applicable[comp] = n_lost >= 8 and n_kept >= 8
    for comp in ALIASES:
        for ans in ALIASES:
            sub = [r for r in rows if r["compressor"] == comp and r["answerer"] == ans
                   and r["truth"] == "DENIED"]
            lost = [r for r in sub if not r["fail_retained"]]
            kept = [r for r in sub if r["fail_retained"]]
            st = dict(
                n_lost=len(lost), n_retained=len(kept),
                decision_lost=frac(sum(r["decision_correct"] for r in lost), len(lost)),
                which_lost=frac(sum(r["which_correct"] for r in lost), len(lost)),
                which_retained=frac(sum(r["which_correct"] for r in kept), len(kept)),
                which_confab_lost=frac(sum(r["which_confab"] for r in lost), len(lost)),
                abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
                abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)),
                incoherent_lost=frac(sum(r["incoherent"] for r in lost), len(lost)),
            )
            pair_stats[f"{comp}->{ans}"] = st

    offdiag = [(c, a) for c in ALIASES for a in ALIASES if c != a and comp_applicable[c]]
    t1_votes = {f"{c}->{a}": bool(pair_stats[f"{c}->{a}"]["which_lost"] <= 1 / 3
                                  and pair_stats[f"{c}->{a}"]["which_retained"] >= 0.7)
                for c, a in offdiag}
    t2_votes = {f"{c}->{a}": bool(pair_stats[f"{c}->{a}"]["decision_lost"] >= 0.6)
                for c, a in offdiag}
    t3_votes = {}
    for c in ALIASES:
        if not comp_applicable[c]:
            continue
        t3_votes[c] = bool(max(pair_stats[f"{c}->{a}"]["which_lost"] for a in ALIASES) <= 0.4)
    preds = {
        "P-T1_debt_transfers": dict(votes=t1_votes, n_pass=sum(t1_votes.values()),
                                    n_applicable=len(t1_votes),
                                    holds=sum(t1_votes.values()) >= min(10, len(t1_votes))),
        "P-T2_verdict_shelf_transfers": dict(votes=t2_votes, n_pass=sum(t2_votes.values()),
                                             n_applicable=len(t2_votes),
                                             holds=sum(t2_votes.values()) >= min(10, len(t2_votes))),
        "P-T3_no_reader_recovers": dict(votes=t3_votes, n_pass=sum(t3_votes.values()),
                                        n_applicable=len(t3_votes),
                                        holds=all(t3_votes.values()) if t3_votes else False),
    }
    cost = {a: round(cost_usd(a, tok[a]), 4) for a in ALIASES}
    print("=== TRANSFER GRID (DENIED cells; rows=compressor, cols=answerer) ===")
    print(f"applicable compressors: {comp_applicable}")
    for metric in ("decision_lost", "which_lost", "which_retained", "abstain_lost",
                   "incoherent_lost", "which_confab_lost"):
        print(f"\n  {metric}:")
        hdr = "    comp\\ans " + "".join(f"{a:>9s}" for a in ALIASES)
        print(hdr)
        for c in ALIASES:
            vals = "".join(f"{pair_stats[f'{c}->{a}'][metric]:9.3f}" for a in ALIASES)
            print(f"    {c:9s}{vals}")
    print("\nPREREGISTERED:")
    for name, p in preds.items():
        print(f"  {name}: {p['n_pass']}/{p['n_applicable']} -> "
              f"{'HOLDS' if p['holds'] else 'FAILS'}")
    print(f"\ntransfer-phase cost by answerer: {cost}  total=${sum(cost.values()):.3f}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(grid="4x4", probes=["decision", "which", "which_abstain"],
                                   corpus="v5 items.jsonl", summaries="v5 cached",
                                   prereg="prereg_transfer.md"),
                       comp_applicable=comp_applicable, pair_stats=pair_stats,
                       preregistered=preds, tokens=tok, cost_usd=cost,
                       total_cost_usd=round(sum(cost.values()), 4)), f, indent=2)
    print(f"wrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "score"])
    ap.add_argument("--answerer", choices=ALIASES, default=None)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(ITEMS)]
    if a.cmd == "run":
        for ans in ([a.answerer] if a.answerer else ALIASES):
            run(ans, items)
    else:
        score(items)


if __name__ == "__main__":
    main()
