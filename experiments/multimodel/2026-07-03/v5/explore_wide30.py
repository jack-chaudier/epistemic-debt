#!/usr/bin/env python3
"""EXPLORATORY (not preregistered): 30-word compression arm for gist-heavy compressors
whose 15-word cells failed the v5 applicability guard (gpt; gemlite if quota allows).
Same corpus and probes as v5; separate artifact files; nonotes reused from v5."""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner3 import (ANS_RE, CHANGE_RE, retained, match_param, parse_which,
                     ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD, REPAIR_SUFFIX)
from providers import MODELS, chat, cost_usd

ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw_wide30.jsonl")
RESULTS = os.path.join(HERE, "wide30_results.json")
HARD_CAP = 800
WL = 30


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["model"], r["item"], r["call"])] = r
    return cache


def api(alias, messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(alias, messages)
    rec = dict(model=key_fn[0], item=key_fn[1], call=key_fn[2], text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(alias, items):
    cache = load_cache()
    for it in items:
        iid = it["id"]
        comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                    f"following incident file to at most {WL} words. A future analyst will need to "
                    f"answer questions about this incident, but you do not know which questions. "
                    f"Output only the compressed notes.")
        summary = api(alias, [{"role": "system", "content": comp_sys},
                              {"role": "user", "content": it["document"]}],
                      cache, (alias, iid, "compress"))
        notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
        for call, suffix in (("decision", ANS_SUFFIX), ("which", WHICH_SUFFIX),
                             ("which_abstain", WHICH_SUFFIX + ABSTAIN_ADD),
                             ("repair", REPAIR_SUFFIX)):
            api(alias, [{"role": "user", "content": notes + suffix}], cache, (alias, iid, call))
        print(f"{alias} {iid} done ({len(cache)})", flush=True)


def score(items, aliases):
    cache = load_cache()
    frac = lambda k, n: k / n if n else float("nan")
    out = {}
    for alias in aliases:
        rows = []
        for it in items:
            iid = it["id"]
            g = lambda call: cache.get((alias, iid, call), {}).get("text")
            summary = g("compress")
            if summary is None:
                continue
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            m = ANS_RE.search(g("decision") or "")
            dec = m.group(1).upper() if m else None
            wp, _ = parse_which(g("which"), it["parameters"])
            wap, _ = parse_which(g("which_abstain"), it["parameters"])
            target = it["failing_param"] or "NONE"
            mm = CHANGE_RE.search(g("repair") or "")
            rows.append(dict(
                truth=it["truth"], summary_words=len(summary.split()),
                fail_retained=retained(summary, fail["value"]) if fail else None,
                decision_correct=dec == it["truth"], which=wp,
                which_correct=wp == target,
                abstained=wap == "INSUFFICIENT_EVIDENCE",
                incoherent=dec == "DENIED" and wp == "NONE",
                repair_specific=bool(mm)))
        den = [r for r in rows if r["truth"] == "DENIED"]
        lost = [r for r in den if not r["fail_retained"]]
        kept = [r for r in den if r["fail_retained"]]
        st = dict(n=len(rows), n_lost=len(lost), n_retained=len(kept),
                  mean_words=sum(r["summary_words"] for r in rows) / max(len(rows), 1),
                  decision_lost=frac(sum(r["decision_correct"] for r in lost), len(lost)),
                  which_lost=frac(sum(r["which_correct"] for r in lost), len(lost)),
                  which_retained=frac(sum(r["which_correct"] for r in kept), len(kept)),
                  abstain_lost=frac(sum(r["abstained"] for r in lost), len(lost)),
                  abstain_retained=frac(sum(r["abstained"] for r in kept), len(kept)),
                  incoherent_lost=frac(sum(r["incoherent"] for r in lost), len(lost)),
                  repair_specific_lost=frac(sum(r["repair_specific"] for r in lost), len(lost)))
        out[alias] = st
        print(alias, json.dumps(st, indent=2))
    tok = {}
    for r in cache.values():
        t = tok.setdefault(r["model"], dict(prompt=0, completion=0))
        t["prompt"] += r["usage"]["prompt"]
        t["completion"] += r["usage"]["completion"]
    cost = {a: round(cost_usd(a, tok[a]), 4) for a in tok}
    with open(RESULTS, "w") as f:
        json.dump(dict(note="EXPLORATORY 30-word arm, not preregistered",
                       stats=out, cost_usd=cost), f, indent=2)
    print("cost:", cost)


if __name__ == "__main__":
    items = [json.loads(l) for l in open(ITEMS)]
    cmd = sys.argv[1]
    if cmd == "run":
        run(sys.argv[2], items)
    else:
        score(items, [a for a in MODELS if (a, items[0]["id"], "compress") in load_cache()
                      or True])
