#!/usr/bin/env python3
"""Abbreviation-robust parameter matching for the clinical domain.

Models (grok especially) answer WHICH with standard medical shorthand — 'K' for
serum potassium, 'BMI' for body mass index, '6MWD' for six-minute walk distance —
even when asked to copy the policy wording. Scoring those as UNMATCHED would
undercount justified accuracy for a purely stylistic reason (a metric confound),
so this resolver recognizes acronyms and a fixed table of canonical clinical
abbreviations, and only accepts a match that is UNIQUE among the item's 12
parameters (conservative: ambiguous shorthand stays UNMATCHED). Applied uniformly
to every arm; on the incident corpus (plain multi-word English names repeated
verbatim) it never fires, so it cannot change incident scoring.
"""
import re
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                "grok-pilots", "2026-07-03", "v3"))
from runner3 import parse_which, match_param

# canonical clinical abbreviations -> substring that identifies the parameter name.
# Keys are lowercased, punctuation-stripped forms of what a model might emit.
ABBREV = {
    "anc": "neutrophil", "plt": "platelet", "crcl": "creatinine clearance",
    "tbili": "bilirubin", "tbil": "bilirubin", "bili": "bilirubin",
    "lvef": "ejection fraction", "ef": "ejection fraction", "ecog": "ecog",
    "hgb": "hemoglobin", "hb": "hemoglobin", "alt": "alanine",
    "sgpt": "alanine", "alb": "albumin", "qtc": "qt interval",
    "fpg": "glucose", "fbg": "glucose", "bmi": "body mass index",
    "sbp": "systolic", "dbp": "diastolic", "wbc": "white blood cell",
    "6mwd": "walk distance", "6mwt": "walk distance", "ntprobnp": "bnp",
    "probnp": "bnp", "bnp": "bnp", "egfr": "glomerular filtration",
    "gfr": "glomerular filtration", "hr": "heart rate", "k": "potassium",
    "qrs": "qrs", "na": "sodium", "tc": "total cholesterol",
    "spo2": "oxygen saturation", "sao2": "oxygen saturation", "o2sat": "oxygen saturation",
    "hba1c": "glycated", "a1c": "glycated", "tg": "triglycerid", "trig": "triglycerid",
    "hdl": "hdl", "cpeptide": "c-peptide", "cr": "serum creatinine",
    "scr": "serum creatinine", "wc": "waist", "tsh": "thyroid",
    "vitd": "vitamin d", "25ohd": "vitamin d", "mmse": "mini-mental",
    "ca": "calcium", "fev1": "fev1", "eos": "eosinophil", "rr": "respiratory rate",
    "dlco": "diffusing capacity", "uacr": "albumin-to-creatinine", "acr": "albumin-to-creatinine",
    "po4": "phosphate", "hco3": "bicarbonate", "bicarb": "bicarbonate",
    "pth": "parathyroid", "ipth": "parathyroid",
}


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def _acronym(name):
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower())
             if w not in {"the", "of", "on", "in", "at", "per", "to", "serum", "total"}]
    return "".join(w[0] for w in words)


def resolve_which(text, params, target):
    """Return the matched parameter name (or NONE/INSUFFICIENT/None/UNMATCHED), applying
    clinical-abbreviation resolution only when the plain matcher returns UNMATCHED."""
    ans, raw = parse_which(text, params)
    if ans != "UNMATCHED" or raw is None:
        return ans
    key = _norm(raw)
    # candidate parameters whose name this token could abbreviate
    hits = []
    for p in params:
        nm = p["name"].lower()
        sub = ABBREV.get(key)
        if sub and sub in nm:
            hits.append(p["name"])
        elif key and key == _acronym(p["name"]):
            hits.append(p["name"])
    hits = sorted(set(hits))
    return hits[0] if len(hits) == 1 else "UNMATCHED"


if __name__ == "__main__":
    # self-test on the shorthand the models actually emitted in smoke tests
    import json
    items = {it["id"]: it for it in map(json.loads, open(
        os.path.join(os.path.dirname(__file__), "items_clinical.jsonl")))}
    cases = [("clin10", "PARAMETER: K", "serum potassium"),
             ("clin04", "PARAMETER: 6MWD", "six-minute walk distance")]
    for iid, txt, expect in cases:
        got = resolve_which(txt, items[iid]["parameters"], expect)
        print(f"{iid}: {txt!r} -> {got!r} (expect {expect!r}) {'OK' if got == expect else 'MISS'}")
