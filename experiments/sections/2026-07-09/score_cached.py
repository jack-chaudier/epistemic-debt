#!/usr/bin/env python3
"""Frozen annexes (prereg_sections.md): P-SEC-3b/3c cached-transfer forecasts and the
P-SEC-1d dual-definition sensitivity check. Reanalysis only, no API. Writes
sections_cached_annex.json."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "experiments", "grok-pilots", "2026-07-03", "v3"))
from runner3 import retained, ANS_RE  # noqa: E402

SEC_MEAS = json.load(open(os.path.join(HERE, "sections_results.json")))
SECTION = {m: v["forecast"]["section_meas"] for m, v in SEC_MEAS["models"].items()}


def dec(t):
    m = ANS_RE.findall(t or "")
    if m:
        return m[-1].upper()
    m = re.findall(r"\b(APPROVED|DENIED)\b", t or "", re.I)
    return m[-1].upper() if m else None


def load(items_path, raw_path):
    items = {it["id"]: it for it in map(json.loads, open(items_path))}
    raw = {}
    for l in open(raw_path):
        r = json.loads(l)
        raw[(r["model"], r["item"], r["call"])] = r["text"]
    return items, raw


def lost_errors(items, raw, model, lost_fn):
    """Signed wrong anchored decisions on evidence-lost cells (both verdict sides)."""
    wrong = []
    for it in items.values():
        s = raw.get((model, it["id"], "compress"))
        if s is None or not lost_fn(it, s):
            continue
        d = dec(raw.get((model, it["id"], "decision")))
        if d in ("APPROVED", "DENIED") and d != it["truth"]:
            wrong.append(d)
    return wrong


def hits(wrong, section):
    n = len(wrong)
    if not n:
        return dict(n=0)
    return dict(n=n, sign_hit=round(sum(w == section for w in wrong) / n, 4),
                truth_marginal=round(max(sum(w == "APPROVED" for w in wrong),
                                         sum(w == "DENIED" for w in wrong)) / n, 4),
                hit_via_sv1=round(sum(w == "APPROVED" for w in wrong) / n, 4))


def official_lost(it, s):
    pol = [p for p in it["parameters"] if p["policy"]]
    if it["truth"] == "DENIED":
        fail = next(p for p in pol if not p["passes"])
        return not retained(s, fail["value"])
    return not all(retained(s, p["value"]) for p in pol)


def numeric_lost(it, s):
    """Sensitivity variant: raw numeric-substring containment instead of retained()."""
    pol = [p for p in it["parameters"] if p["policy"]]
    if it["truth"] == "DENIED":
        fail = next(p for p in pol if not p["passes"])
        return str(fail["value"]) not in s
    return not all(str(p["value"]) in s for p in pol)


out = dict(section_from_surgical_measurement=SECTION)

# P-SEC-3c: cached 2026-07-06 compression cells (all 3 models)
di, dr = load(os.path.join(REPO, "experiments", "domains", "2026-07-06", "items.jsonl"),
              os.path.join(REPO, "experiments", "domains", "2026-07-06", "responses_raw.jsonl"))
out["p_sec_3c_compression"] = {m: hits(lost_errors(di, dr, m, official_lost), SECTION[m])
                               for m in ("grok", "haiku", "gpt")}

# P-SEC-3b: cached realdoc lost cells (haiku, gpt) — control arm (suffix _ctrl: blind
# compaction; the fusion arm is an intervention, not a debt condition)
ri, rr0 = load(os.path.join(REPO, "experiments", "realdoc", "2026-07-08", "items.jsonl"),
               os.path.join(REPO, "experiments", "realdoc", "2026-07-08", "responses_raw.jsonl"))
rr = {}
for (m, i, c), t in rr0.items():
    if c in ("compress_ctrl", "decision_ctrl"):
        rr[(m, i, c.replace("_ctrl", ""))] = t
out["p_sec_3b_realdoc"] = {m: hits(lost_errors(ri, rr, m, official_lost), SECTION.get(m, "DENIED"))
                           for m in ("haiku", "gpt")}

# P-SEC-1d: dual-definition sensitivity on cached compression cells (DENIED-side approve bias)
sens = {}
for m in ("grok", "haiku", "gpt"):
    row = {}
    for name, fn in (("official", official_lost), ("numeric", numeric_lost)):
        app = n = 0
        for it in di.values():
            if it["truth"] != "DENIED":
                continue
            s = dr.get((m, it["id"], "compress"))
            if s is None or not fn(it, s):
                continue
            d = dec(dr.get((m, it["id"], "decision")))
            if d in ("APPROVED", "DENIED"):
                n += 1
                app += (d == "APPROVED")
        row[name] = dict(n=n, approve=round(app / n, 4) if n else None)
    row["sign_consistent"] = (row["official"]["approve"] is not None
                              and row["numeric"]["approve"] is not None
                              and ((row["official"]["approve"] - 0.5)
                                   * (row["numeric"]["approve"] - 0.5) > 0))
    sens[m] = row
out["p_sec_1d_sensitivity"] = sens

json.dump(out, open(os.path.join(HERE, "sections_cached_annex.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
