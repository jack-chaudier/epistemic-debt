#!/usr/bin/env python3
"""Deterministic re-parse of cached WHICH / WHICH-ABSTAIN responses (no API calls).

parse_which_v2: last occurrence of `PARAMETER\\s*:` (colon required) instead of the
first occurrence of `PARAMETER:?` — the v1 regex hits the plural word "parameters."
in prose and drops verbose readers' final `PARAMETER: NONE` line. See README.md.

Recomputes the headline cells (WHICH accuracy, confabulation, incoherence, abstention)
per model / transfer cell, original vs v2, on DENIED items. Writes reparse_results.json.
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "multimodel", "2026-07-03")
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
from runner3 import match_param, parse_which  # v1 parser, for the side-by-side

PARAM_COLON_RE = re.compile(r"PARAMETER\s*:\s*\**\s*([^\n*]+)", re.I)


def parse_which_v2(text, params):
    matches = PARAM_COLON_RE.findall(text or "")
    if not matches:
        return None, None
    raw = matches[-1].strip().rstrip(".")
    up = raw.upper().replace(" ", "_")
    if "INSUFFICIENT" in up:
        return "INSUFFICIENT_EVIDENCE", raw
    if up.startswith("NONE"):
        return "NONE", raw
    return match_param(raw, params) or "UNMATCHED", raw


def load_items():
    path = os.path.join(MULTI, "v5", "items.jsonl")
    return {it["id"]: it for it in map(json.loads, open(path))}


def cells(rows, items, texts, keyfn):
    """rows: scored-csv DENIED rows carrying decision + fail_retained metadata."""
    out = []
    for r in rows:
        it = items[r["item"]]
        target = it["failing_param"]
        rec = dict(key=keyfn(r), item=r["item"], lost=r["fail_retained"] == "False",
                   decision=r["decision"] if "decision" in r else None)
        for call in ("which", "which_abstain"):
            txt = texts.get((keyfn(r), r["item"], call))
            v1, _ = parse_which(txt, it["parameters"])
            v2, _ = parse_which_v2(txt, it["parameters"])
            rec[call + "_v1"], rec[call + "_v2"] = v1, v2
        rec["target"] = target
        out.append(rec)
    return out


def summarize(recs, ver):
    def agg(sub):
        n = len(sub)
        if n == 0:
            return dict(n=0)
        w = lambda r: r["which_" + ver]
        a = lambda r: r["which_abstain_" + ver]
        return dict(
            n=n,
            which_correct=sum(w(r) == r["target"] for r in sub),
            which_none=sum(w(r) == "NONE" for r in sub),
            which_confab=sum(w(r) not in (None, "NONE", "INSUFFICIENT_EVIDENCE", "UNMATCHED")
                             and w(r) != r["target"] for r in sub),
            which_unmatched=sum(w(r) in (None, "UNMATCHED") for r in sub),
            incoherent=sum(r["decision"] == "DENIED" and w(r) == "NONE" for r in sub),
            abstained=sum(a(r) == "INSUFFICIENT_EVIDENCE" for r in sub),
        )
    return dict(lost=agg([r for r in recs if r["lost"]]),
                retained=agg([r for r in recs if not r["lost"]]))


def main():
    items = load_items()
    results = {}

    # v5 -------------------------------------------------------------------
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "v5", "responses_raw.jsonl"))):
        if r["call"] in ("which", "which_abstain"):
            texts[(r["model"], r["item"], r["call"])] = r["text"]
    rows = [r for r in csv.DictReader(open(os.path.join(MULTI, "v5", "scored.csv")))
            if r["truth"] == "DENIED"]
    for model in ("grok", "haiku", "gpt", "gemlite"):
        sub = [r for r in rows if r["model"] == model]
        recs = cells(sub, items, texts, lambda r: r["model"])
        results[f"v5/{model}"] = {v: summarize(recs, v) for v in ("v1", "v2")}

    # transfer ---------------------------------------------------------------
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "transfer", "responses_raw.jsonl"))):
        if r["call"] in ("which", "which_abstain"):
            texts[((r["compressor"], r["answerer"]), r["item"], r["call"])] = r["text"]
    rows = [r for r in csv.DictReader(open(os.path.join(MULTI, "transfer", "scored.csv")))
            if r["truth"] == "DENIED"]
    # self-pairs were served from the v5 cache and have no transfer raw records;
    # they are covered by the v5 section above
    pairs = sorted({(r["compressor"], r["answerer"]) for r in rows
                    if any(k[0] == (r["compressor"], r["answerer"]) for k in texts)})
    for pair in pairs:
        sub = [r for r in rows if (r["compressor"], r["answerer"]) == pair]
        recs = cells(sub, items, texts, lambda r: (r["compressor"], r["answerer"]))
        results[f"transfer/{pair[0]}->{pair[1]}"] = {v: summarize(recs, v) for v in ("v1", "v2")}

    # reasoning-reader --------------------------------------------------------
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "reasoning-reader", "responses_raw.jsonl"))):
        if r["call"] in ("which", "which_abstain"):
            texts[("gpt5mini", r["item"], r["call"])] = r["text"]
    rrows = [r for r in csv.DictReader(open(os.path.join(MULTI, "reasoning-reader", "scored.csv")))
             if r["truth"] == "DENIED"]
    for r in rrows:
        r["decision"] = "DENIED" if r["decision_correct"] == "True" else "APPROVED"
    recs = cells(rrows, items, texts, lambda r: "gpt5mini")
    results["reasoning/gpt5mini"] = {v: summarize(recs, v) for v in ("v1", "v2")}

    out = os.path.join(HERE, "reparse_results.json")
    json.dump(results, open(out, "w"), indent=1)
    for k, v in results.items():
        l1, l2 = v["v1"]["lost"], v["v2"]["lost"]
        if not l1["n"]:
            continue
        print(f"{k:28s} lost n={l1['n']:2d}  "
              f"correct {l1['which_correct']}->{l2['which_correct']}  "
              f"NONE {l1['which_none']}->{l2['which_none']}  "
              f"confab {l1['which_confab']}->{l2['which_confab']}  "
              f"unmatched {l1['which_unmatched']}->{l2['which_unmatched']}  "
              f"incoh {l1['incoherent']}->{l2['incoherent']}  "
              f"abstain {l1['abstained']}->{l2['abstained']}")
    print("wrote", out)


if __name__ == "__main__":
    main()
