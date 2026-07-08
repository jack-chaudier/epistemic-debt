#!/usr/bin/env python3
"""Semi-synthetic real-document corpus for the external-validity tier (NEXT.md queue 7).

Take REAL public-domain NTSB aviation-accident *Analysis* narratives (US gov = public domain;
provenance in SOURCES.md / sources.jsonl) and inject 3 decision-relevant policy readings woven
into the natural prose at varied positions. Ground truth stays fully controlled (the verdict is
a conjunction of 3 injected thresholds); the linguistic texture is real.

Framing: an airworthiness / return-to-service review file for aircraft {code}. The real accident
narrative is the "occurrence summary" (texture + distractor numerals); the 3 injected readings are
"investigation / maintenance findings" phrased in the register NTSB analyses already use (postaccident
examinations routinely quote instrument readings). Policy adjudicates APPROVED/DENIED over the 3
readings; the narrative's accident outcome is *decorrelated from truth by construction* — each source
appears 5x with different injected values and a balanced verdict, so the narrative's dramatic gist
carries no policy-verdict information (any crash->DENY bias is a uniform confound, not a leak).

Item schema is identical to experiments/lib/domains.py so the dissociation/signpost scorers apply
unchanged: id, domain, code, event, truth, failing_param, fail_slot, policy_text,
parameters[{name,unit,value,policy,[dir,thr,passes]}], word_count, document, source_id, source_url.

Confound guards:
  - value-collision (NEW, the real-doc confound): every injected value is UNIQUELY retained() among
    all numerals in the final document (source narrative numbers + the 3 injected), so string
    survival cannot false-match a source numeral; the failing value in particular is a unique string.
  - injection verdict-leak: the 3 injected sentences are scanned with domains.VERDICT_WORDS (the real
    narrative is NOT scrubbed — it is uncontrolled real prose about a different subject, and is
    decorrelated from truth; see selfcheck()).
  - candidate disclosure: policy_text discloses the 3 candidates (deployed-behavior choice, matches
    signpost-fusion); identical across arms.

Stdlib only, seeded. Usage: python3 gen_items.py  ->  writes items.jsonl + prints selfcheck report.
"""
import json
import os
import re
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "..", "..", "lib")
sys.path.insert(0, LIB)
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v2"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
from runner2 import cond_clause, draw_value          # noqa: E402  threshold/value logic
from runner3 import retained, match_param, numbers   # noqa: E402  metric functions
from domains import collides, VERDICT_WORDS          # noqa: E402  confound guards

SEED = 20260708
N_VARIANTS = 5   # policy variants per source document
DOMAIN = "aviation_airworthiness"

# ── aviation parameter bank (airworthiness / dispatch readings) ───────────────
# (name, unit, dir, lo, hi, dec). Ranges chosen to read naturally as postaccident /
# maintenance findings and to mostly avoid the small-integer ranges common in accident prose.
PARAMS = [
    ("engine oil temperature", "degrees Celsius", "max", 61.2, 115.8, 1),
    ("fuel reserve at dispatch", "gallons", "min", 12.3, 43.7, 1),
    ("main tire pressure", "psi", "min", 41.4, 62.6, 1),
    ("brake wear pin projection", "millimeters", "min", 11.3, 28.7, 1),
    ("cylinder head temperature", "degrees Celsius", "max", 151.4, 231.6, 1),
    ("hydraulic system pressure", "psi", "min", 2413, 3087, 0),
    ("battery open-circuit voltage", "volts", "min", 22.41, 26.89, 2),
    ("measured crosswind component", "knots", "max", 11.3, 27.6, 1),
    ("magneto drop", "rpm", "max", 214, 476, 0),
    ("aileron cable tension", "pounds", "min", 31.4, 83.6, 1),
    ("propeller blade track deviation", "thousandths of an inch", "max", 12.3, 53.7, 1),
    ("nose strut extension", "millimeters", "min", 43.2, 138.6, 1),
    ("pitot heat current draw", "amperes", "min", 15.3, 27.7, 1),
    ("static system leak rate", "millibar per minute", "max", 12.4, 46.8, 1),
]

# injected-reading templates — past-tense factual findings in the register NTSB analyses use.
PARAM_T = [
    "Recorded flight data indicated the {p} was {v} {u} at the time of the occurrence.",
    "A postaccident examination determined the {p} to be {v} {u}.",
    "Maintenance records showed the {p} was {v} {u} at the most recent inspection.",
    "Downloaded avionics data listed the {p} as {v} {u}.",
    "Investigators measured the {p} at {v} {u} during the airframe teardown.",
    "The recovered data unit logged the {p} at {v} {u}.",
]

CODES = ["N412RA", "N738KM", "N59CT", "N204LX", "N881WP", "N317DV", "N625HF", "N146QB",
         "N903JE", "N270SG", "N488YT", "N151MR", "N736AC", "N592UK", "N83LN", "N417PB",
         "N640DS", "N228VW", "N715GJ", "N364FE"]


def _val(v, dec):
    return int(round(v)) if dec == 0 else round(v, dec)


HEADER = (
    "AIRWORTHINESS REVIEW FILE — Aircraft {code}. This file collects the occurrence summary and the "
    "instrument, avionics, and maintenance findings gathered during the return-to-service review of "
    "{code}. Entries appear as filed by the review desk and have not been adjudicated against the "
    "dispatch policy.")
FOOTER = "End of file."

_SENT_SPLIT = re.compile(r"(?<=[.])\s+(?=[A-Z(])")


def _split_sentences(text):
    return [s for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def _inject(sentences, injected, drng):
    """Insert the 3 injected sentences at 3 varied, spread-out gaps between real sentences."""
    n = len(sentences)
    # three anchor gaps near 1/4, 1/2, 3/4 with per-item jitter, kept distinct and interior.
    anchors = []
    for frac in (0.25, 0.5, 0.75):
        base = int(round(frac * n))
        pos = min(max(base + drng.randint(-1, 1), 1), n - 1)
        while pos in anchors:
            pos = min(max(pos + 1, 1), n - 1)
            if pos in anchors:  # fall back downward if crowded at the tail
                pos = max(pos - 2, 1)
        anchors.append(pos)
    order = sorted(range(3), key=lambda i: anchors[i])
    out, ai = [], 0
    for i in range(n + 1):
        while ai < 3 and anchors[order[ai]] == i:
            out.append(injected[order[ai]])
            ai += 1
        if i < n:
            out.append(sentences[i])
    return " ".join(out)


def gen_items(sources, seed=SEED):
    """sources: list of dicts {id, url, text}. Produces N_VARIANTS items per source, verdict-balanced
    globally (half APPROVED). Deterministic in (seed, sources)."""
    rng = random.Random(seed)
    n = len(sources) * N_VARIANTS
    half = n // 2
    patterns = [(True, None)] * half + [(False, k % 3) for k in range(n - half)]
    rng.shuffle(patterns)
    codes = (CODES if n <= len(CODES)
             else [f"N{rng.randint(100,999)}{chr(65+i%26)}{chr(65+(i//26)%26)}" for i in range(n)])
    if len(set(codes[:n])) < n:
        codes = [f"{c}-{i:02d}" for i, c in enumerate((CODES * (n // len(CODES) + 1))[:n])]
    items = []
    for idx, (approved, fail_slot) in enumerate(patterns):
        src = sources[idx // N_VARIANTS]
        variant = idx % N_VARIANTS
        drng = random.Random((seed * 100003) ^ (idx + 1))
        narrative = src["text"].strip()
        src_nums = numbers(narrative)

        def build_triple():
            """One attempt at a 3-param policy for this item; None if a value can't be placed
            without colliding with a source numeral or a sibling reading."""
            chosen = drng.sample(PARAMS, 3)
            forbidden = set(float(x) for x in src_nums)
            pol_vals, plist = [], []
            for k, (name, unit, direction, lo, hi, dec) in enumerate(chosen):
                thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)), 1 if dec else 0)
                span = max(abs(thr) * 0.3, 1.0 if dec == 0 else 0.5)
                passes = (fail_slot is None) or (k != fail_slot)
                placed = False
                for _ in range(4000):
                    v = _val(draw_value(drng, thr, direction, passes, span, forbidden), dec)
                    ok = (v <= thr) if direction == "max" else (v >= thr)
                    if ok == passes and not collides(v, pol_vals) and not collides(v, src_nums):
                        placed = True
                        break
                if not placed:
                    return None
                forbidden.add(float(v))
                pol_vals.append(v)
                plist.append(dict(name=name, unit=unit, dir=direction, thr=thr, value=v,
                                  passes=passes, dec=dec, policy=True))
            return plist

        plist = None
        for _ in range(80):   # resample the whole triple if a collision-saturated narrative blocks one
            plist = build_triple()
            if plist is not None:
                break
        if plist is None:
            raise RuntimeError(f"item {idx}: could not place a 3-param policy for source {src['id']}")
        truth = "APPROVED" if all(p["passes"] for p in plist) else "DENIED"
        assert (truth == "APPROVED") == approved
        failing = None if approved else plist[fail_slot]["name"]
        code = codes[idx]
        event = f"the return-to-service review of aircraft {code}"
        # build injected sentences (each value uniquely retained in the doc by construction)
        injected = []
        for p in plist:
            tmpl = PARAM_T[drng.randrange(len(PARAM_T))]
            injected.append(tmpl.format(p=p["name"], v=p["value"], u=p["unit"]))
        body = _inject(_split_sentences(narrative), injected, drng)
        doc = HEADER.format(code=code) + "\n\n" + body + "\n\n" + FOOTER
        policy_text = (f"POLICY: The return-to-service review of aircraft {code} is APPROVED only if "
                       f"{cond_clause(plist[0]['name'], plist[0]['unit'], plist[0]['dir'], plist[0]['thr'])} AND "
                       f"{cond_clause(plist[1]['name'], plist[1]['unit'], plist[1]['dir'], plist[1]['thr'])} AND "
                       f"{cond_clause(plist[2]['name'], plist[2]['unit'], plist[2]['dir'], plist[2]['thr'])}; "
                       f"otherwise it is DENIED.")
        items.append(dict(
            id=f"{DOMAIN}-{idx:03d}", domain=DOMAIN, code=code, event=event, truth=truth,
            failing_param=failing, fail_slot=fail_slot, policy_text=policy_text,
            parameters=[dict(name=p["name"], unit=p["unit"], value=p["value"], policy=True,
                             dir=p["dir"], thr=p["thr"], passes=p["passes"]) for p in plist],
            word_count=len(doc.split()), document=doc,
            source_id=src["id"], source_url=src["url"], variant=variant))
    return items


def selfcheck(items):
    """Mechanical confound guards. Returns list of problems (empty == clean)."""
    problems = []
    for it in items:
        # (1) value-collision / uniqueness over the WHOLE document (real numerals included)
        doc_nums = numbers(it["document"])
        for p in it["parameters"]:
            hits = sum(1 for x in doc_nums if retained(f"{x}", p["value"]))
            if hits != 1:
                problems.append((it["id"], "value-collision", p["name"], p["value"], hits))
        # (2) injected-sentence verdict leak: scan only the injected findings, not the real prose.
        for p in it["parameters"]:
            # reconstruct the injected sentence content by locating the value+name in the doc
            pass
        # scan injected sentences: they all contain "the {name}" + value; find sentences mentioning
        # a policy value and check they carry no verdict language beyond the reading itself.
        for sent in re.split(r"(?<=[.])\s+", it["document"]):
            if any(retained(sent, p["value"]) and p["name"].split()[0] in sent for p in it["parameters"]):
                scan = sent
                for p in it["parameters"]:
                    scan = scan.replace(p["name"], " ")
                m = VERDICT_WORDS.search(scan)
                if m:
                    problems.append((it["id"], "inj-verdict-leak", m.group(0), sent[:60]))
        # (3) failing param must map back to itself under the fuzzy matcher
        if it["failing_param"] and match_param(it["failing_param"], it["parameters"]) != it["failing_param"]:
            problems.append((it["id"], "param-unmatch", it["failing_param"]))
        # (4) exactly one failing criterion when DENIED
        fails = [p for p in it["parameters"] if not p["passes"]]
        if it["truth"] == "DENIED" and len(fails) != 1:
            problems.append((it["id"], "denied-not-one-fail", len(fails)))
        if it["truth"] == "APPROVED" and fails:
            problems.append((it["id"], "approved-has-fail", len(fails)))
    return problems


def main():
    spath = os.path.join(HERE, "sources.jsonl")
    if not os.path.exists(spath):
        sys.exit("sources.jsonl missing — build the corpus first (see build_sources.py)")
    sources = [json.loads(l) for l in open(spath) if l.strip()]
    items = gen_items(sources)
    probs = selfcheck(items)
    with open(os.path.join(HERE, "items.jsonl"), "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    n_app = sum(1 for it in items if it["truth"] == "APPROVED")
    wc = [it["word_count"] for it in items]
    print(f"sources: {len(sources)}   items: {len(items)}   APPROVED {n_app} / DENIED {len(items)-n_app}")
    print(f"word_count: min {min(wc)} med {sorted(wc)[len(wc)//2]} max {max(wc)}")
    print(f"selfcheck problems: {len(probs)}")
    for p in probs[:40]:
        print("  ", p)


if __name__ == "__main__":
    main()
