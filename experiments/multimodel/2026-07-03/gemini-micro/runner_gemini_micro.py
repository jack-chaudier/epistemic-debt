#!/usr/bin/env python3
"""Gemini micro-arm: stratified reader test on grok's v5 summaries under the
20-requests/day/model free-tier quota. One probe channel per Gemini model bucket.
See prereg_gemini.md (fixed before any call)."""
import json, math, os, random, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
V5 = os.path.join(HERE, "..", "v5")
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
sys.path.insert(0, os.path.join(HERE, ".."))
from runner3 import (ANS_RE, retained, parse_which,
                     ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD)
from providers import _key

RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "gemini_micro_results.json")
HARD_CAP = 100
PACE = 6.5  # free-tier RPM is also small; pace every call

CHANNELS = {
    "which": dict(suffix=WHICH_SUFFIX,
                  buckets=["gemini-3-flash-preview", "gemini-3.1-flash-lite",
                           "gemini-2.5-pro", "gemini-3-pro-preview"]),
    "which_abstain": dict(suffix=WHICH_SUFFIX + ABSTAIN_ADD,
                          buckets=["gemini-3.1-flash-lite", "gemini-3-flash-preview",
                                   "gemini-2.5-pro", "gemini-3-pro-preview"]),
    "decision": dict(suffix=ANS_SUFFIX,
                     buckets=["gemini-2.5-pro", "gemini-3-pro-preview",
                              "gemini-3-flash-preview", "gemini-3.1-flash-lite"]),
}


def gemini_call(model, prompt):
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": 800}}
    if model.startswith("gemini-2.5"):
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"x-goog-api-key": _key("GEMINI_API_KEY"),
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.loads(r.read())
    except urllib.error.HTTPError as e:
        detail = e.read()[:400].decode(errors="replace")
        if e.code == 429 and "PerDay" in detail:
            return None, "QUOTA_DAY"
        if e.code in (429, 500, 503):
            return None, "TRANSIENT"
        raise
    cand = d.get("candidates", [{}])[0]
    text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    u = d.get("usageMetadata", {})
    return dict(text=text, usage=dict(prompt=u.get("promptTokenCount", 0),
                                      completion=u.get("candidatesTokenCount", 0))), None


def sample_items():
    items = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(V5, "items.jsonl"))}
    grok_sums = {}
    for line in open(os.path.join(V5, "responses_raw.jsonl")):
        r = json.loads(line)
        if r["model"] == "grok" and r["call"] == "compress":
            grok_sums[r["item"]] = r["text"]
    lost, kept = [], []
    for iid, it in sorted(items.items()):
        if it["truth"] != "DENIED":
            continue
        pol = [p for p in it["parameters"] if p["policy"]]
        fail = next(p for p in pol if not p["passes"])
        (kept if retained(grok_sums[iid], fail["value"]) else lost).append(iid)
    rng = random.Random(7777)
    pick_lost = sorted(rng.sample(lost, 12))
    assert len(kept) == 8
    return items, grok_sums, pick_lost, sorted(kept)


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["channel"], r["bucket"], r["item"])] = r
    return cache


def run():
    items, sums, lost, kept = sample_items()
    sample = lost + kept
    print(f"sample: {len(lost)} lost + {len(kept)} retained")
    cache = load_cache()
    for chan, cfg in CHANNELS.items():
        done_bucket = None
        for b in cfg["buckets"]:
            if all((chan, b, iid) in cache for iid in sample):
                done_bucket = b
                break
        buckets = [done_bucket] if done_bucket else cfg["buckets"]
        for bucket in buckets:
            ok = True
            for iid in sample:
                if (chan, bucket, iid) in cache:
                    continue
                if len(cache) + 1 > HARD_CAP:
                    sys.exit("HARD CAP")
                notes = (items[iid]["policy_text"] + "\n\nCompressed case notes:\n"
                         + sums[iid] + "\n\n" + cfg["suffix"])
                res = err = None
                for attempt in range(4):
                    time.sleep(PACE)
                    res, err = gemini_call(bucket, notes)
                    if err != "TRANSIENT":
                        break
                    time.sleep(10 * (attempt + 1))
                if err == "QUOTA_DAY" or (res is None and err == "TRANSIENT"):
                    print(f"{chan}: bucket {bucket} exhausted ({err}); falling back", flush=True)
                    ok = False
                    break
                rec = dict(channel=chan, bucket=bucket, item=iid,
                           text=res["text"], usage=res["usage"])
                with open(RAW, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                cache[(chan, bucket, iid)] = rec
            if ok:
                print(f"{chan}: completed in bucket {bucket}", flush=True)
                break


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def score():
    items, sums, lost, kept = sample_items()
    sample = lost + kept
    cache = load_cache()
    complete = {}
    for chan, cfg in CHANNELS.items():
        for b in cfg["buckets"]:
            if all((chan, b, iid) in cache for iid in sample):
                complete[chan] = b
                break
    print("completed channels:", complete)
    frac = lambda k, n: k / n if n else float("nan")
    out = dict(sample=dict(lost=lost, retained=kept), channels=complete, cells={},
               preds={}, discarded_partial_calls=0)
    tok = dict(prompt=0, completion=0)
    used = {(c, complete[c]) for c in complete}
    for r in cache.values():
        tok["prompt"] += r["usage"]["prompt"]
        tok["completion"] += r["usage"]["completion"]
        if (r["channel"], r["bucket"]) not in used:
            out["discarded_partial_calls"] += 1

    res = {}
    for iid in sample:
        it = items[iid]
        target = it["failing_param"]
        row = dict(lost=iid in lost)
        if "which" in complete:
            wp, _ = parse_which(cache[("which", complete["which"], iid)]["text"],
                                it["parameters"])
            row["which"] = wp
            row["which_correct"] = wp == target
        if "which_abstain" in complete:
            wa, _ = parse_which(cache[("which_abstain", complete["which_abstain"], iid)]["text"],
                                it["parameters"])
            row["abstained"] = wa == "INSUFFICIENT_EVIDENCE"
        if "decision" in complete:
            m = ANS_RE.search(cache[("decision", complete["decision"], iid)]["text"] or "")
            row["decision_correct"] = bool(m) and m.group(1).upper() == it["truth"]
        res[iid] = row
    L = [res[i] for i in lost]
    K = [res[i] for i in kept]
    cells = {}
    if "which" in complete:
        cells["which_lost"] = [sum(r["which_correct"] for r in L), len(L)]
        cells["which_retained"] = [sum(r["which_correct"] for r in K), len(K)]
    if "which_abstain" in complete:
        cells["abstain_lost"] = [sum(r["abstained"] for r in L), len(L)]
        cells["abstain_retained"] = [sum(r["abstained"] for r in K), len(K)]
    if "decision" in complete:
        cells["decision_lost"] = [sum(r["decision_correct"] for r in L), len(L)]
        cells["decision_retained"] = [sum(r["decision_correct"] for r in K), len(K)]
    out["cells"] = {k: dict(k=v[0], n=v[1], p=frac(*v), ci95=wilson(*v))
                    for k, v in cells.items()}
    if "which" in complete:
        out["preds"]["P-G1"] = dict(
            criteria="which_lost<=1/3 AND which_retained>=0.7",
            passed=bool(frac(*cells["which_lost"]) <= 1 / 3
                        and frac(*cells["which_retained"]) >= 0.7))
    if "which_abstain" in complete:
        out["preds"]["P-G2"] = dict(
            criteria="abstain_lost>=0.5 AND abstain_retained<=0.25",
            passed=bool(frac(*cells["abstain_lost"]) >= 0.5
                        and frac(*cells["abstain_retained"]) <= 0.25))
    if "decision" in complete:
        out["preds"]["P-G3"] = dict(
            criteria="decision_lost>=0.6",
            passed=bool(frac(*cells["decision_lost"]) >= 0.6))
    out["tokens"] = tok
    out["cost_usd"] = 0.0  # free tier
    for k, v in out["cells"].items():
        print(f"  {k:18s}: {v['k']}/{v['n']} = {v['p']:.3f}  CI [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]")
    for k, v in out["preds"].items():
        print(f"  {k}: {'PASS' if v['passed'] else 'FAIL'}")
    with open(RESULTS, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    (run if sys.argv[1] == "run" else score)()
