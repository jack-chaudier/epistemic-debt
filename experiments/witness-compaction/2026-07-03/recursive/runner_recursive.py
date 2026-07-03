#!/usr/bin/env python3
"""Phase C: recursive compaction chain (doc->80->40->15) vs direct (doc->15), grok,
30 DENIED v5 items. See prereg_recursive.md (fixed before any call)."""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "..", "multimodel", "2026-07-03")
V5 = os.path.join(MULTI, "v5")
CURVE_RAW = os.path.join(HERE, "..", "curve", "responses_raw.jsonl")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, MULTI)
from runner3 import ANS_RE, retained, parse_which, ANS_SUFFIX, WHICH_SUFFIX
from providers import chat, cost_usd

RAW = os.path.join(HERE, "responses_raw.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "recursive_results.json")
HARD_CAP = 500
ALIAS = "grok"
CHAIN = [80, 40, 15]


def comp_sys(wl, kind):
    src = "incident file" if kind == "doc" else "case notes"
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following {src} to at most {wl} words. A future analyst will need to "
            f"answer questions about this incident, but you do not know which questions. "
            f"Output only the compressed notes.")


def load_items():
    return [it for it in map(json.loads, open(os.path.join(V5, "items.jsonl")))
            if it["truth"] == "DENIED"]


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["arm"], r["item"], r["call"])] = r
    return cache


def load_curve_direct():
    """direct arm = phase-B 15w compress + probes (identical prompt/model/items)."""
    out = {}
    if os.path.exists(CURVE_RAW):
        for line in open(CURVE_RAW):
            r = json.loads(line)
            if r["wl"] == 15:
                out[(r["item"], r["call"])] = r["text"]
    return out


def api(messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit("HARD CAP")
    text, usage = chat(ALIAS, messages)
    rec = dict(arm=key_fn[0], item=key_fn[1], call=key_fn[2], text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


def run(items):
    cache = load_cache()
    for it in items:
        iid = it["id"]
        prev, kind = it["document"], "doc"
        for wl in CHAIN:
            prev = api([{"role": "system", "content": comp_sys(wl, kind)},
                        {"role": "user", "content": prev}], cache, ("chain", iid, f"compress{wl}"))
            kind = "notes"
        notes = it["policy_text"] + "\n\nCompressed case notes:\n" + prev + "\n\n"
        api([{"role": "user", "content": notes + ANS_SUFFIX}], cache, ("chain", iid, "decision"))
        api([{"role": "user", "content": notes + WHICH_SUFFIX}], cache, ("chain", iid, "which"))
        print(f"{iid} done ({len(cache)})", flush=True)


def score(items):
    cache = load_cache()
    direct = load_curve_direct()
    frac = lambda k, n: k / n if n else float("nan")
    rows = []
    for it in items:
        iid = it["id"]
        pol = [p for p in it["parameters"] if p["policy"]]
        fail = next(p for p in pol if not p["passes"])
        for arm in ("direct", "chain"):
            if arm == "direct":
                summary = direct.get((iid, "compress"))
                dtxt = direct.get((iid, "decision"))
                wtxt = direct.get((iid, "which"))
            else:
                g = lambda call: cache.get(("chain", iid, call), {}).get("text")
                summary = g("compress15")
                dtxt, wtxt = g("decision"), g("which")
            if summary is None:
                continue
            m = ANS_RE.search(dtxt or "")
            wp, _ = parse_which(wtxt, it["parameters"])
            row = dict(arm=arm, item=iid, words=len(summary.split()),
                       ret_policy=sum(retained(summary, p["value"]) for p in pol) / 3,
                       fail_retained=retained(summary, fail["value"]),
                       decision_correct=(m.group(1).upper() if m else None) == "DENIED",
                       which_correct=wp == it["failing_param"])
            if arm == "chain":
                for wl in CHAIN[:2]:
                    s = cache.get(("chain", iid, f"compress{wl}"), {}).get("text", "")
                    row[f"ret_{wl}"] = sum(retained(s, p["value"]) for p in pol) / 3
            rows.append(row)
    with open(SCORED, "w", newline="") as f:
        fields = sorted({k for r in rows for k in r}, key=lambda k: (k != "arm", k))
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    st = {}
    for arm in ("direct", "chain"):
        sub = [r for r in rows if r["arm"] == arm]
        st[arm] = dict(
            n=len(sub), words=sum(r["words"] for r in sub) / len(sub),
            retention=sum(r["ret_policy"] for r in sub) / len(sub),
            fail_survival=frac(sum(r["fail_retained"] for r in sub), len(sub)),
            decision=frac(sum(r["decision_correct"] for r in sub), len(sub)),
            which=frac(sum(r["which_correct"] for r in sub), len(sub)))
    chain_sub = [r for r in rows if r["arm"] == "chain"]
    decay = dict(gen80=sum(r["ret_80"] for r in chain_sub) / len(chain_sub),
                 gen40=sum(r["ret_40"] for r in chain_sub) / len(chain_sub),
                 gen15=st["chain"]["retention"])
    d, c = st["direct"], st["chain"]
    preds = {
        "P-C1_dpi_sanity": dict(direct=d["retention"], chain=c["retention"],
                                passed=bool(c["retention"] <= d["retention"] + 0.05)),
        "P-C2_compounding": dict(direct=d["retention"], chain=c["retention"],
                                 passed=bool(c["retention"] <= d["retention"] - 0.10)),
        "P-C3_gist_corrupts": dict(direct=d["decision"], chain=c["decision"],
                                   passed=bool(c["decision"] <= d["decision"] - 0.10)),
    }
    tok = dict(prompt=0, completion=0)
    for r in cache.values():
        tok["prompt"] += r["usage"]["prompt"]
        tok["completion"] += r["usage"]["completion"]
    cost = round(cost_usd(ALIAS, tok), 4)
    for arm, s in st.items():
        print(f"{arm:7s}: words={s['words']:.1f} retention={s['retention']:.3f} "
              f"fail_survival={s['fail_survival']:.3f} decision={s['decision']:.3f} "
              f"which={s['which']:.3f}")
    print("chain decay:", {k: round(v, 3) for k, v in decay.items()})
    for k, v in preds.items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")
    print(f"cost: ${cost}")
    with open(RESULTS, "w") as f:
        json.dump(dict(design=dict(model=ALIAS, chain=CHAIN, direct="phase-B 15w cache",
                                   n_items=len(items), prereg="prereg_recursive.md"),
                       arms=st, chain_decay=decay, preds=preds, tokens=tok, cost_usd=cost),
                  f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    items = load_items()
    (run if sys.argv[1] == "run" else score)(items)
