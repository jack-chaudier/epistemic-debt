#!/usr/bin/env python3
"""v3: right answer vs known reason, within-item. Contract-blind compaction (40 words),
DENIED items have exactly one failing policy parameter; WHICH/WHICH-ABSTAIN/REPAIR probes
plus a no-notes prior baseline. 6 calls per item, N=40 -> 240 calls (cap 300).
"""
import argparse, csv, json, os, random, re, sys, time
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2"))
from runner2 import (DOMAINS, ADJ, NOUN, PARAM_T, nn_distractor, cond_clause,
                     draw_value, full_name)

KEY_PATH = os.path.join(HERE, "..", "..", "secrets", "xai_key")
ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SUMS = os.path.join(HERE, "summaries.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
MODEL = "grok-4-1-fast-non-reasoning"
URL = "https://api.x.ai/v1/chat/completions"
HARD_CAP = 300

# ---------------------------------------------------------------- generation


def gen_items():
    rng = random.Random(333)
    patterns = [(True, None)] * 20 + [(False, k % 3) for k in range(20)]  # fail slot 7/7/6
    rng.shuffle(patterns)
    codes = rng.sample([a + " " + b for a in ADJ for b in NOUN], 40)
    used_sentences, items = set(), []
    for i, (approved, fail_slot) in enumerate(patterns):
        dom = DOMAINS[i % 6]
        drng = random.Random(7000 + i)
        chosen = drng.sample(dom["params"], 12)
        pol_idx = sorted(drng.sample(range(12), 3))
        forbidden = set()
        plist = []
        for k, pi in enumerate(pol_idx):
            name, unit, direction, lo, hi, dec = chosen[pi]
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)), 1)
            forbidden.add(float(thr))
            span = max(abs(thr) * 0.3, 0.5)
            p = (fail_slot is None) or (k != fail_slot)
            v = draw_value(drng, thr, direction, p, span, forbidden)
            forbidden.add(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=True, dir=direction,
                              thr=thr, value=v, passes=p))
        for pi in range(12):
            if pi in pol_idx:
                continue
            name, unit, direction, lo, hi, dec = chosen[pi]
            for _ in range(300):
                v = round(drng.uniform(lo, hi), 2)
                if abs(v - round(v)) < 0.005 or any(abs(v - f) < 1e-9 for f in forbidden):
                    continue
                break
            else:
                raise RuntimeError("nonpolicy value draw failed")
            forbidden.add(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=False, value=v))
        plist.sort(key=lambda d: d["idx"])
        pol = [d for d in plist if d["policy"]]
        truth = "APPROVED" if all(d["passes"] for d in pol) else "DENIED"
        assert (truth == "APPROVED") == approved
        failing = None if approved else pol[fail_slot]["name"]
        code = codes[i]
        event = dom["event"].format(code=code)
        intro = (f"INCIDENT REVIEW FILE — Operation {code}. This file collects readings and "
                 f"observations logged during {event}. Entries appear in the order received by "
                 f"the Operation {code} duty desk and have not been prioritized or adjudicated.")
        param_sents = []
        for d in plist:
            for _ in range(60):
                s = drng.choice(PARAM_T).format(p=d["name"], v=d["value"], u=d["unit"],
                                                name=full_name(drng))
                if s not in used_sentences:
                    used_sentences.add(s)
                    param_sents.append(s)
                    break
            else:
                raise RuntimeError("param sentence uniqueness failed")
        body = param_sents + [nn_distractor(drng, used_sentences) for _ in range(15)]
        drng.shuffle(body)
        paras, k = [], 0
        while k < len(body):
            step = drng.choice([3, 4, 5])
            paras.append(" ".join(body[k:k + step]))
            k += step
        doc = intro + "\n\n" + "\n\n".join(paras) + "\n\nEnd of file."
        policy_text = (f"POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
                       f"{cond_clause(pol[0]['name'], pol[0]['unit'], pol[0]['dir'], pol[0]['thr'])} AND "
                       f"{cond_clause(pol[1]['name'], pol[1]['unit'], pol[1]['dir'], pol[1]['thr'])} AND "
                       f"{cond_clause(pol[2]['name'], pol[2]['unit'], pol[2]['dir'], pol[2]['thr'])}; "
                       f"otherwise it is DENIED.")
        items.append(dict(
            id=f"v3item{i:02d}", domain=dom["domain"], code=code, event=event, truth=truth,
            failing_param=failing, fail_slot=fail_slot, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            word_count=len(doc.split()), document=doc))
    return items

# ---------------------------------------------------------------- API


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["item"], r["call"], r["wl"])] = r
    return cache


def api(messages, cache, key_fn):
    if key_fn in cache:
        return cache[key_fn]["text"]
    if len(cache) + 1 > HARD_CAP:
        print("HARD BUDGET CAP REACHED — aborting.")
        sys.exit(2)
    with open(KEY_PATH) as f:
        key = f.read().strip()
    body = json.dumps({"model": MODEL, "temperature": 0, "messages": messages}).encode()
    for attempt in range(3):
        req = urllib.request.Request(URL, data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            break
        except urllib.error.HTTPError as e:
            code, detail = e.code, e.read()[:300].decode(errors="replace")
            if code == 429 or code >= 500:
                if attempt == 2:
                    raise RuntimeError(f"API failed after retries: {code} {detail}")
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"API error {code}: {detail}")
        except urllib.error.URLError:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
    text = data["choices"][0]["message"]["content"]
    u = data.get("usage", {})
    rec = dict(item=key_fn[0], call=key_fn[1], wl=key_fn[2], text=text,
               usage=dict(prompt=u.get("prompt_tokens", 0),
                          completion=u.get("completion_tokens", 0),
                          total=u.get("total_tokens", 0)))
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


ANS_SUFFIX = ("Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED|DENIED, "
              "then EVIDENCE: and quote or paraphrase the specific facts (with numbers) that determine it.")
WHICH_SUFFIX = ("Per the policy, if the decision is DENIED, name the single parameter whose reading "
                "caused the denial. Reply exactly: PARAMETER: <name> or PARAMETER: NONE if the "
                "decision is APPROVED.")
ABSTAIN_ADD = (" If the notes do not contain enough information to determine this, reply exactly: "
               "PARAMETER: INSUFFICIENT_EVIDENCE.")
REPAIR_SUFFIX = ("What is the minimal single-parameter change that would flip the decision? "
                 "Reply exactly: CHANGE: <parameter> to <value>.")
NONOTES_SUFFIX = ("Based only on the policy and general plausibility, guess: ANSWER: APPROVED|DENIED "
                  "and PARAMETER: <name|NONE>.")


def run_items(items, start, end, wl, denied_only=False, limit=None):
    cache = load_cache()
    todo = [it for it in items[start:end] if not denied_only or it["truth"] == "DENIED"]
    if limit:
        todo = todo[:limit]
    for it in todo:
        iid = it["id"]
        comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                    f"following incident file to at most {wl} words. A future analyst will need to "
                    f"answer questions about this incident, but you do not know which questions. "
                    f"Output only the compressed notes.")
        summary = api([{"role": "system", "content": comp_sys},
                       {"role": "user", "content": it["document"]}], cache, (iid, "compress", wl))
        pol = it["policy_text"]
        notes = pol + "\n\nCompressed case notes:\n" + summary + "\n\n"
        api([{"role": "user", "content": notes + ANS_SUFFIX}], cache, (iid, "decision", wl))
        api([{"role": "user", "content": notes + WHICH_SUFFIX}], cache, (iid, "which", wl))
        api([{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
            cache, (iid, "which_abstain", wl))
        api([{"role": "user", "content": notes + REPAIR_SUFFIX}], cache, (iid, "repair", wl))
        api([{"role": "user", "content": pol + "\n\n" + NONOTES_SUFFIX}], cache, (iid, "nonotes", 0))
        print(f"{iid} done ({len(cache)} calls cached)", flush=True)

# ---------------------------------------------------------------- scoring

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
ANS_RE = re.compile(r"ANSWER:?\s*\**\s*(APPROVED|DENIED)", re.I)
PARAM_RE = re.compile(r"PARAMETER:?\s*\**\s*([^\n*]+)", re.I)
CHANGE_RE = re.compile(r"CHANGE:?\s*\**\s*(.+?)\s+to\s+(-?\d+(?:\.\d+)?)", re.I)
GIST_RE = re.compile(r"anomal|exceed|below|out[- ]of[- ]spec|out of range|marginal|elevated|"
                     r"degraded|warning|abnormal|deviat|breach|violat|fail|flag|too (high|low)|"
                     r"noncompliant|non-compliant", re.I)
STOP = {"the", "a", "an", "of", "on", "in", "at", "per", "rate", "level", "index", "reading"}


def numbers(text):
    return [float(m) for m in NUM_RE.findall(text.replace(",", ""))]


def retained(text, v):
    for x in numbers(text):
        if abs(x - v) < 1e-9 or (v != 0 and abs(x - v) / abs(v) <= 0.01):
            return True
        if any(abs(x - round(v, k)) < 1e-9 for k in (0, 1)):
            return True
    return False


def words_of(name):
    return set(re.findall(r"[a-z]+", name.lower())) - STOP


def match_param(text, params):
    """Map free text to one of the item's param names; tolerant of abbreviations ('cert')."""
    tw = set(re.findall(r"[a-z]+", text.lower())) - STOP
    if not tw:
        return None
    best, score = None, 0.0
    for p in params:
        pw = words_of(p["name"])
        hit = sum(1 for t in tw if any(
            t == w or (len(t) >= 4 and (w.startswith(t) or t.startswith(w))) for w in pw))
        prec = hit / len(tw)
        rec = hit / max(len(pw), 1)
        s = prec + 0.1 * rec
        if s > score:
            best, score = p["name"], s
    return best if score >= 0.6 else None


def parse_which(text, params):
    m = PARAM_RE.search(text or "")
    if not m:
        return None, None
    raw = m.group(1).strip().rstrip(".")
    up = raw.upper().replace(" ", "_")
    if "INSUFFICIENT" in up:
        return "INSUFFICIENT_EVIDENCE", raw
    if up.startswith("NONE"):
        return "NONE", raw
    return match_param(raw, params) or "UNMATCHED", raw


def score(items, wl):
    cache = load_cache()
    rows, anomalies = [], []
    tok = dict(prompt=0, completion=0, total=0)
    for r in cache.values():
        for k in tok:
            tok[k] += r["usage"][k]
    with open(SUMS, "w") as sf:
        for it in items:
            iid = it["id"]
            g = lambda call, w: cache.get((iid, call, w), {}).get("text")
            summary = g("compress", wl)
            if summary is None:
                continue
            sf.write(json.dumps(dict(item=iid, wl=wl, summary=summary)) + "\n")
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            row = dict(item=iid, domain=it["domain"], truth=it["truth"],
                       failing_param=it["failing_param"], summary_words=len(summary.split()),
                       ret_policy=sum(retained(summary, p["value"]) for p in pol) / 3,
                       fail_retained=retained(summary, fail["value"]) if fail else None,
                       any_policy_lost=not all(retained(summary, p["value"]) for p in pol),
                       gist_flag=bool(GIST_RE.search(summary)))
            # decision
            dtxt = g("decision", wl)
            m = ANS_RE.search(dtxt or "")
            row["decision"] = m.group(1).upper() if m else None
            if dtxt and not m:
                anomalies.append((iid, "decision", dtxt[:160]))
            row["decision_correct"] = row["decision"] == it["truth"]
            # which / which_abstain
            for call in ("which", "which_abstain"):
                txt = g(call, wl)
                ans, raw = parse_which(txt, it["parameters"])
                if txt and ans is None:
                    anomalies.append((iid, call, txt[:160]))
                row[call] = ans
                row[call + "_raw"] = raw
            target = it["failing_param"] or "NONE"
            row["which_correct"] = row["which"] == target
            row["which_confab"] = (row["which"] not in (None, "NONE", "INSUFFICIENT_EVIDENCE",
                                                        "UNMATCHED") and row["which"] != target)
            row["abstained"] = row["which_abstain"] == "INSUFFICIENT_EVIDENCE"
            row["which_abstain_correct"] = row["which_abstain"] == target
            # repair
            rtxt = g("repair", wl)
            m = CHANGE_RE.search(rtxt or "")
            row["repair_param"], row["repair_ok"] = None, False
            if m:
                pname = match_param(m.group(1), it["parameters"])
                val = float(m.group(2))
                row["repair_param"] = pname
                p = next((p for p in pol if p["name"] == pname), None)
                if p is not None:
                    crosses = (val <= p["thr"]) if p["dir"] == "max" else (val >= p["thr"])
                    if it["truth"] == "DENIED":
                        row["repair_ok"] = (pname == target) and crosses
                    else:
                        row["repair_ok"] = not crosses  # any policy param pushed out of spec
            elif rtxt:
                anomalies.append((iid, "repair", rtxt[:160]))
            # no-notes baseline
            ntxt = g("nonotes", 0)
            m = ANS_RE.search(ntxt or "")
            row["nn_decision"] = m.group(1).upper() if m else None
            nna, _ = parse_which(ntxt or "", it["parameters"])
            row["nn_param"] = nna
            row["nn_decision_correct"] = row["nn_decision"] == it["truth"]
            row["nn_param_correct"] = nna == target
            rows.append(row)
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    frac = lambda xs: (f"{sum(xs)}/{len(xs)}" if xs else "0/0")
    print(f"\n=== v3 REPORT (n={n}, wl={wl}) ===")
    den = [r for r in rows if r["truth"] == "DENIED"]
    app = [r for r in rows if r["truth"] == "APPROVED"]
    print(f"mean summary words {sum(r['summary_words'] for r in rows)/n:.1f}; "
          f"policy retention (tolerant) {sum(r['ret_policy'] for r in rows)/n:.3f}")
    print("\nPRIMARY: DENIED items by failing-value retention in summary")
    for cond, lab in ((True, "retained"), (False, "lost    ")):
        sub = [r for r in den if r["fail_retained"] == cond]
        print(f"  {lab} (n={len(sub)}): decision {frac([r['decision_correct'] for r in sub])}"
              f"  WHICH {frac([r['which_correct'] for r in sub])}"
              f"  REPAIR {frac([r['repair_ok'] for r in sub])}")
    lost = [r for r in den if not r["fail_retained"]]
    print("\nLost-cell 2x2 (WHICH correct?) x (abstain-variant abstained?):")
    for wc in (True, False):
        for ab in (True, False):
            c = sum(1 for r in lost if r["which_correct"] == wc and r["abstained"] == ab)
            print(f"  which_correct={wc} abstained={ab}: {c}")
    print(f"  confabulated-which (specific wrong param) in lost cell: "
          f"{frac([r['which_confab'] for r in lost])}")
    print(f"  abstentions in retained DENIED cell: "
          f"{frac([r['abstained'] for r in den if r['fail_retained']])}")
    print("\nAPPROVED control (no shelf):")
    print(f"  decision {frac([r['decision_correct'] for r in app])}, "
          f"WHICH=NONE {frac([r['which_correct'] for r in app])}, "
          f"REPAIR {frac([r['repair_ok'] for r in app])}, "
          f"abstain {frac([r['abstained'] for r in app])}")
    for cond, lab in ((False, "all policy retained"), (True, "some policy lost   ")):
        sub = [r for r in app if r["any_policy_lost"] == cond]
        if sub:
            print(f"    {lab} (n={len(sub)}): decision {frac([r['decision_correct'] for r in sub])}, "
                  f"WHICH=NONE {frac([r['which_correct'] for r in sub])}")
    print("\nGist leakage in DENIED summaries (qualitative out-of-spec language):")
    for cond, lab in ((True, "retained"), (False, "lost    ")):
        sub = [r for r in den if r["fail_retained"] == cond]
        print(f"  {lab}: {frac([r['gist_flag'] for r in sub])}")
    print("\nNo-notes baseline: decision "
          f"{frac([r['nn_decision_correct'] for r in rows])}, parameter "
          f"{frac([r['nn_param_correct'] for r in rows])} "
          f"(DENIED param floor: {frac([r['nn_param_correct'] for r in den])})")
    print(f"\ntokens: prompt={tok['prompt']} completion={tok['completion']} total={tok['total']}")
    print(f"anomalies: {len(anomalies)}")
    for a in anomalies:
        print("  ", a)
    for r in [r for r in den if not r["fail_retained"]][:3]:
        print(f"\n--- lost-witness DENIED {r['item']} (failing: {r['failing_param']}) ---")
        print("SUMMARY:", cache[(r["item"], "compress", wl)]["text"])
        print("WHICH  :", (cache[(r["item"], "which", wl)]["text"] or "").strip()[:250])
        print("ABSTAIN:", (cache[(r["item"], "which_abstain", wl)]["text"] or "").strip()[:250])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "run", "score"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=40)
    ap.add_argument("--wl", type=int, default=40)
    ap.add_argument("--denied-only", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "gen":
        items = gen_items()
        with open(ITEMS, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        print(f"generated {len(items)} items; words min={min(it['word_count'] for it in items)} "
              f"max={max(it['word_count'] for it in items)} "
              f"approved={sum(it['truth'] == 'APPROVED' for it in items)} "
              f"fail slots={[sum(it['fail_slot'] == k for it in items) for k in (0, 1, 2)]}")
        return
    items = [json.loads(l) for l in open(ITEMS)]
    if a.cmd == "run":
        run_items(items, a.start, a.end, a.wl, a.denied_only, a.limit)
    else:
        score(items, a.wl)


if __name__ == "__main__":
    main()
