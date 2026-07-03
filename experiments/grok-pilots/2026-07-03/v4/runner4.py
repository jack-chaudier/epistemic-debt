#!/usr/bin/env python3
"""v4: preregistered confirmatory run of the v3 dissociation. N=60, single 15-word budget,
6 calls per item (COMPRESS, DECISION, WHICH, WHICH-ABSTAIN, REPAIR, NO-NOTES) = 360 calls.
"""
import argparse, csv, json, math, os, random, re, sys, time
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2"))
sys.path.insert(0, os.path.join(HERE, "..", "v3"))
from runner2 import DOMAINS, ADJ, NOUN, PARAM_T, nn_distractor, cond_clause, draw_value, full_name
from runner3 import (NUM_RE, ANS_RE, PARAM_RE, CHANGE_RE, GIST_RE, numbers, retained,
                     match_param, parse_which, ANS_SUFFIX, WHICH_SUFFIX, ABSTAIN_ADD,
                     REPAIR_SUFFIX, NONOTES_SUFFIX)

KEY_PATH = os.path.join(HERE, "..", "..", "secrets", "xai_key")
ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SUMS = os.path.join(HERE, "summaries.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
RESULTS = os.path.join(HERE, "v4_results.json")
MODEL = "grok-4-1-fast-non-reasoning"
URL = "https://api.x.ai/v1/chat/completions"
HARD_CAP = 400
WL = 15


def gen_items():
    rng = random.Random(4242)
    patterns = [(True, None)] * 30 + [(False, k % 3) for k in range(30)]  # fail slots 10/10/10
    rng.shuffle(patterns)
    codes = rng.sample([a + " " + b for a in ADJ for b in NOUN], 60)
    used_sentences, items = set(), []
    for i, (approved, fail_slot) in enumerate(patterns):
        dom = DOMAINS[i % 6]
        drng = random.Random(9000 + i)
        chosen = drng.sample(dom["params"], 12)
        pol_idx = sorted(drng.sample(range(12), 3))
        forbidden, plist = set(), []
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
            id=f"v4item{i:02d}", domain=dom["domain"], code=code, event=event, truth=truth,
            failing_param=failing, fail_slot=fail_slot, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            word_count=len(doc.split()), document=doc))
    return items


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


def run_items(items, start, end):
    cache = load_cache()
    for it in items[start:end]:
        iid = it["id"]
        comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                    f"following incident file to at most {WL} words. A future analyst will need to "
                    f"answer questions about this incident, but you do not know which questions. "
                    f"Output only the compressed notes.")
        summary = api([{"role": "system", "content": comp_sys},
                       {"role": "user", "content": it["document"]}], cache, (iid, "compress", WL))
        pol = it["policy_text"]
        notes = pol + "\n\nCompressed case notes:\n" + summary + "\n\n"
        api([{"role": "user", "content": notes + ANS_SUFFIX}], cache, (iid, "decision", WL))
        api([{"role": "user", "content": notes + WHICH_SUFFIX}], cache, (iid, "which", WL))
        api([{"role": "user", "content": notes + WHICH_SUFFIX + ABSTAIN_ADD}],
            cache, (iid, "which_abstain", WL))
        api([{"role": "user", "content": notes + REPAIR_SUFFIX}], cache, (iid, "repair", WL))
        api([{"role": "user", "content": pol + "\n\n" + NONOTES_SUFFIX}], cache, (iid, "nonotes", 0))
        print(f"{iid} done ({len(cache)} calls cached)", flush=True)


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def score(items):
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
            summary = g("compress", WL)
            if summary is None:
                continue
            sf.write(json.dumps(dict(item=iid, wl=WL, summary=summary)) + "\n")
            pol = [p for p in it["parameters"] if p["policy"]]
            fail = next((p for p in pol if not p["passes"]), None)
            row = dict(item=iid, domain=it["domain"], truth=it["truth"],
                       failing_param=it["failing_param"], summary_words=len(summary.split()),
                       ret_policy=sum(retained(summary, p["value"]) for p in pol) / 3,
                       fail_retained=retained(summary, fail["value"]) if fail else None,
                       any_policy_lost=not all(retained(summary, p["value"]) for p in pol),
                       gist_flag=bool(GIST_RE.search(summary)))
            dtxt = g("decision", WL)
            m = ANS_RE.search(dtxt or "")
            row["decision"] = m.group(1).upper() if m else None
            if dtxt and not m:
                anomalies.append((iid, "decision", dtxt[:160]))
            row["decision_correct"] = row["decision"] == it["truth"]
            for call in ("which", "which_abstain"):
                txt = g(call, WL)
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
            rtxt = g("repair", WL)
            m = CHANGE_RE.search(rtxt or "")
            row["repair_param"], row["repair_ok"], row["repair_specific"] = None, False, False
            if m:
                pname = match_param(m.group(1), it["parameters"])
                val = float(m.group(2))
                row["repair_param"] = pname
                row["repair_specific"] = True
                p = next((p for p in pol if p["name"] == pname), None)
                if p is not None:
                    crosses = (val <= p["thr"]) if p["dir"] == "max" else (val >= p["thr"])
                    if it["truth"] == "DENIED":
                        row["repair_ok"] = (pname == target) and crosses
                    else:
                        row["repair_ok"] = not crosses
            elif rtxt:
                anomalies.append((iid, "repair", rtxt[:160]))
            ntxt = g("nonotes", 0)
            m = ANS_RE.search(ntxt or "") or re.search(r"\b(APPROVED|DENIED)\b", ntxt or "", re.I)
            row["nn_decision"] = m.group(1).upper() if m else None
            nna, _ = parse_which(ntxt or "", it["parameters"])
            row["nn_param"] = nna
            row["nn_decision_correct"] = row["nn_decision"] == it["truth"]
            row["nn_param_correct"] = nna == target
            row["incoherent"] = row["decision"] == "DENIED" and row["which"] == "NONE"
            rows.append(row)
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    den = [r for r in rows if r["truth"] == "DENIED"]
    app = [r for r in rows if r["truth"] == "APPROVED"]
    lost = [r for r in den if not r["fail_retained"]]
    kept = [r for r in den if r["fail_retained"]]
    app_lost = [r for r in app if r["any_policy_lost"]]
    app_kept = [r for r in app if not r["any_policy_lost"]]
    cnt = lambda xs, f: sum(1 for r in xs if f(r))
    frac = lambda k, n: k / n if n else float("nan")

    cells = dict(
        n=len(rows), n_denied=len(den), n_approved=len(app),
        n_lost=len(lost), n_retained=len(kept),
        mean_summary_words=sum(r["summary_words"] for r in rows) / len(rows),
        mean_policy_retention=sum(r["ret_policy"] for r in rows) / len(rows),
        decision_lost=[cnt(lost, lambda r: r["decision_correct"]), len(lost)],
        decision_retained=[cnt(kept, lambda r: r["decision_correct"]), len(kept)],
        which_lost=[cnt(lost, lambda r: r["which_correct"]), len(lost)],
        which_retained=[cnt(kept, lambda r: r["which_correct"]), len(kept)],
        repair_lost=[cnt(lost, lambda r: r["repair_ok"]), len(lost)],
        repair_retained=[cnt(kept, lambda r: r["repair_ok"]), len(kept)],
        repair_specific_lost=[cnt(lost, lambda r: r["repair_specific"]), len(lost)],
        which_confab_lost=[cnt(lost, lambda r: r["which_confab"]), len(lost)],
        abstain_lost=[cnt(lost, lambda r: r["abstained"]), len(lost)],
        abstain_retained=[cnt(kept, lambda r: r["abstained"]), len(kept)],
        incoherent_lost=[cnt(lost, lambda r: r["incoherent"]), len(lost)],
        incoherent_retained=[cnt(kept, lambda r: r["incoherent"]), len(kept)],
        approved_decision_lost=[cnt(app_lost, lambda r: r["decision_correct"]), len(app_lost)],
        approved_decision_retained=[cnt(app_kept, lambda r: r["decision_correct"]), len(app_kept)],
        approved_which_none=[cnt(app, lambda r: r["which_correct"]), len(app)],
        gist_lost=[cnt(lost, lambda r: r["gist_flag"]), len(lost)],
        gist_retained=[cnt(kept, lambda r: r["gist_flag"]), len(kept)],
        nonotes_decision=[cnt(rows, lambda r: r["nn_decision_correct"]), len(rows)],
        nonotes_decision_denied=[cnt(den, lambda r: r["nn_decision_correct"]), len(den)],
        nonotes_param_denied=[cnt(den, lambda r: r["nn_param_correct"]), len(den)],
    )
    dl = frac(*cells["decision_lost"])
    wl_ = frac(*cells["which_lost"])
    wr = frac(*cells["which_retained"])
    nn_d = frac(*cells["nonotes_decision_denied"])
    preds = {
        "P-A_shelf": dict(
            criteria="decision_lost>=0.6 AND decision_lost>=nonotes_denied_floor AND which_lost<=0.33 AND which_retained>=0.8",
            values=dict(decision_lost=dl, nonotes_denied_floor=nn_d, which_lost=wl_,
                        which_retained=wr),
            passed=bool(dl >= 0.6 and dl >= nn_d and wl_ <= 0.33 and wr >= 0.8)),
        "P-B_channel_asymmetry": dict(
            criteria="approved_decision_under_some_loss < denied_decision_under_loss",
            values=dict(approved_lost=frac(*cells["approved_decision_lost"]), denied_lost=dl),
            passed=bool(frac(*cells["approved_decision_lost"]) < dl)),
        "P-C_confabulation_locus": dict(
            criteria="which_confab_lost<0.25 AND repair_specific_lost>=0.75",
            values=dict(which_confab_lost=frac(*cells["which_confab_lost"]),
                        repair_specific_lost=frac(*cells["repair_specific_lost"])),
            passed=bool(frac(*cells["which_confab_lost"]) < 0.25
                        and frac(*cells["repair_specific_lost"]) >= 0.75)),
        "P-D_honesty_uptake": dict(
            criteria="abstain_lost>=0.5 AND abstain_retained<=0.1",
            values=dict(abstain_lost=frac(*cells["abstain_lost"]),
                        abstain_retained=frac(*cells["abstain_retained"])),
            passed=bool(frac(*cells["abstain_lost"]) >= 0.5
                        and frac(*cells["abstain_retained"]) <= 0.1)),
    }
    cis = {k: dict(k=cells[k][0], n=cells[k][1],
                   p=frac(*cells[k]), ci95=wilson(cells[k][0], cells[k][1]))
           for k in ("decision_lost", "which_lost", "which_retained", "repair_lost")}

    print(f"\n=== v4 PREREGISTERED REPORT (n={len(rows)}, wl={WL}) ===")
    print(f"mean summary words {cells['mean_summary_words']:.1f}; "
          f"policy retention {cells['mean_policy_retention']:.3f}; "
          f"cells: DENIED retained={len(kept)} lost={len(lost)}; "
          f"APPROVED all-retained={len(app_kept)} some-lost={len(app_lost)}")
    print("\nDENIED primary cells:")
    for k in ("decision_lost", "decision_retained", "which_lost", "which_retained",
              "repair_lost", "repair_retained"):
        print(f"  {k:18s}: {cells[k][0]}/{cells[k][1]}")
    print("headline Wilson 95% CIs:")
    for k, v in cis.items():
        print(f"  {k:15s}: {v['k']}/{v['n']} = {v['p']:.3f}  CI [{v['ci95'][0]:.3f}, {v['ci95'][1]:.3f}]")
    print("\nsecondary counts:")
    for k in ("which_confab_lost", "repair_specific_lost", "abstain_lost", "abstain_retained",
              "incoherent_lost", "incoherent_retained", "approved_decision_lost",
              "approved_decision_retained", "approved_which_none", "gist_lost", "gist_retained",
              "nonotes_decision", "nonotes_decision_denied", "nonotes_param_denied"):
        print(f"  {k:26s}: {cells[k][0]}/{cells[k][1]}")
    print("\nPREREGISTERED PREDICTIONS:")
    for name, p in preds.items():
        print(f"  {name}: {'PASS' if p['passed'] else 'FAIL'}  ({p['criteria']})")
        print(f"      values: " + ", ".join(f"{k}={v:.3f}" for k, v in p["values"].items()))
    print(f"\ntokens: prompt={tok['prompt']} completion={tok['completion']} total={tok['total']}")
    print(f"anomalies: {len(anomalies)}")
    for a in anomalies:
        print("  ", a)
    for r in lost[:3]:
        print(f"\n--- lost-witness DENIED {r['item']} (failing: {r['failing_param']}) ---")
        print("SUMMARY:", cache[(r["item"], "compress", WL)]["text"])
        print("WHICH  :", (cache[(r["item"], "which", WL)]["text"] or "").strip()[:200])
        print("ABSTAIN:", (cache[(r["item"], "which_abstain", WL)]["text"] or "").strip()[:200])

    with open(RESULTS, "w") as f:
        json.dump(dict(
            design=dict(n_items=60, approved=30, denied=30, denied_fail_slots=[10, 10, 10],
                        compression_word_limit=WL, model=MODEL, temperature=0,
                        seed="Random(4242) corpus / Random(9000+i) per item",
                        calls_per_item=6, retention_scoring="rounding-tolerant (1% or displayed precision)"),
            preregistered_predictions=preds,
            cells=cells, headline_wilson_ci=cis,
            tokens=tok, anomalies=len(anomalies)), f, indent=2)
    print(f"\nwrote {RESULTS}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "run", "score"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=60)
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
        run_items(items, a.start, a.end)
    else:
        score(items)


if __name__ == "__main__":
    main()
