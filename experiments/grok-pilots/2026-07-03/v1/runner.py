#!/usr/bin/env python3
"""Debt->brittleness pilot: procedural item generation + Grok API runs + scoring.

Subcommands:
  gen                       generate items.jsonl (seeded, no LLM)
  run --start A --end B --wl W   run the 5 calls per item for items[A:B] with compression word limit W
  score --wl W              score responses at word limit W, write summaries.jsonl / scored.csv, print report
"""
import argparse, csv, json, os, random, re, sys, time
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(HERE, "..", "secrets", "xai_key")
ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SUMS = os.path.join(HERE, "summaries.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
MODEL = "grok-4-1-fast-non-reasoning"
URL = "https://api.x.ai/v1/chat/completions"
HARD_CAP = 200

# ---------------------------------------------------------------- generation

DOMAINS = [
    dict(domain="satellite launch", event="the launch of the {code} payload",
         params=[("sensor calibration offset", "mrad", "max", 0.3, 0.9, 2),
                 ("backup battery charge", "percent", "min", 70, 92, 1),
                 ("lead operator certification rating", "points", "min", 3.0, 4.5, 1),
                 ("guidance regression pass rate", "percent", "min", 92, 99, 1),
                 ("fairing pressure differential", "kPa", "max", 2.0, 6.0, 1)]),
    dict(domain="chemical batch release", event="release of the {code} production batch",
         params=[("residual solvent concentration", "ppm", "max", 40, 120, 1),
                 ("batch purity assay", "percent", "min", 95, 99, 1),
                 ("cooling loop flow rate", "L/min", "min", 30, 80, 1),
                 ("catalyst moisture content", "percent", "max", 1.0, 4.0, 1),
                 ("QA composite audit score", "points", "min", 80, 95, 1)]),
    dict(domain="rail switch deployment", event="deployment of the {code} switch assembly",
         params=[("actuator response latency", "ms", "max", 120, 400, 1),
                 ("track gauge deviation", "mm", "max", 1.5, 5.0, 1),
                 ("interlock relay voltage", "volts", "min", 22, 26, 1),
                 ("ballast compaction index", "points", "min", 60, 90, 1),
                 ("signal alignment error", "degrees", "max", 0.4, 1.6, 2)]),
    dict(domain="data-center failover", event="the {code} failover cutover",
         params=[("replication lag", "seconds", "max", 4, 18, 1),
                 ("UPS reserve charge", "percent", "min", 65, 90, 1),
                 ("standby CPU headroom", "percent", "min", 25, 55, 1),
                 ("packet loss on the interconnect", "percent", "max", 0.5, 2.5, 2),
                 ("generator fuel reserve", "hours", "min", 8, 24, 1)]),
    dict(domain="vaccine lot release", event="release of the {code} vaccine lot",
         params=[("cumulative cold-chain excursion", "minutes", "max", 20, 90, 1),
                 ("potency assay result", "percent of label claim", "min", 90, 105, 1),
                 ("endotoxin level", "EU/mL", "max", 0.5, 2.0, 2),
                 ("fill-volume deviation", "percent", "max", 1.0, 3.5, 2),
                 ("stability composite score", "points", "min", 75, 95, 1)]),
    dict(domain="bridge load test", event="certification of the {code} span load test",
         params=[("peak midspan deflection", "mm", "max", 20, 60, 1),
                 ("anchor bolt torque", "N-m", "min", 300, 500, 1),
                 ("concrete core strength", "MPa", "min", 30, 55, 1),
                 ("vibration amplitude", "mm/s", "max", 3.0, 9.0, 2),
                 ("bearing seat rotation", "degrees", "max", 0.5, 1.8, 2)]),
]

ADJ = ["Crimson", "Amber", "Cobalt", "Ivory", "Onyx", "Saffron", "Viridian", "Slate", "Auburn",
       "Cerulean", "Umber", "Scarlet", "Pewter", "Indigo", "Maroon", "Teal", "Ochre", "Sable",
       "Copper", "Silver", "Golden", "Hazel", "Jade", "Coral", "Ashen", "Bronze", "Violet",
       "Emerald", "Garnet", "Opal", "Topaz", "Quartz", "Basalt", "Granite", "Flint", "Birch"]
NOUN = ["Falcon", "Heron", "Badger", "Lantern", "Anvil", "Compass", "Harbor", "Summit", "Meridian",
        "Beacon", "Osprey", "Marten", "Paddock", "Quarry", "Sextant", "Trellis", "Vanguard",
        "Windlass", "Yardarm", "Zephyr", "Bulwark", "Cairn", "Dynamo", "Ember", "Fathom",
        "Gantry", "Hollow", "Isthmus", "Jetty", "Keystone", "Lattice", "Mallet", "Nimbus",
        "Orchard", "Pinnacle", "Rampart"]
FIRST = ["Marisol", "Dietrich", "Anouk", "Tobias", "Ingrid", "Ravi", "Celeste", "Bram", "Yuki",
         "Odalys", "Ferran", "Greta", "Hamid", "Ilona", "Jasper", "Katya", "Lorenzo", "Mireille",
         "Nikolai", "Oksana", "Priya", "Quentin", "Rosalind", "Stellan", "Tamsin", "Ulric",
         "Vesna", "Wendell", "Ximena", "Yusuf", "Zelda", "Arne", "Beatrix", "Casimir", "Delphine"]
LAST = ["Okonkwo", "Berglund", "Castellanos", "Drummond", "Eriksen", "Farrow", "Galanis",
        "Hartwig", "Iqbal", "Jorgensen", "Kowalczyk", "Lindqvist", "Marchetti", "Nakamura",
        "Oduya", "Petrakis", "Quintero", "Rasmussen", "Soriano", "Thackeray", "Ulloa",
        "Vanterpool", "Wachowski", "Xanthos", "Ybarra", "Zielinski", "Abernathy", "Bellweather",
        "Cormorant", "Dunleavy", "Eastgate", "Fairbanks"]
TEAMS = ["logistics", "facilities", "telemetry", "documentation", "night operations", "safety",
         "procurement", "maintenance", "communications", "training", "inventory", "transport"]
SHIFTS = ["morning", "afternoon", "overnight", "weekend", "second", "swing", "early", "relief"]
DATES = ["March 4", "March 11", "March 19", "April 2", "April 8", "April 15", "April 23",
         "May 1", "May 7", "May 14", "May 20", "May 29", "June 3", "June 10", "June 17",
         "February 12", "February 26", "January 30", "June 24", "July 1"]
EQUIP = ["forklift", "badge scanner", "HVAC chiller", "spare parts cabinet", "loading dock crane",
         "coffee dispenser", "intercom console", "shredder", "label printer", "pallet wrapper",
         "service elevator", "floor scrubber", "conference projector", "keycard encoder",
         "backup printer", "air compressor", "utility cart", "document scanner"]
ROOMS = ["annex B", "the west mezzanine", "corridor 7", "the staging bay", "dock 3",
         "the records vault", "hangar 2", "the north stairwell", "briefing room 4",
         "the equipment cage", "sublevel 1", "the visitor lobby"]
WEATHER = ["light drizzle", "gusty crosswinds", "patchy fog", "unseasonable warmth",
           "a brief hailstorm", "steady overcast", "high humidity", "a cold snap",
           "intermittent showers", "clear skies"]
TOPICS = ["parking allocation", "cafeteria menus", "visitor escorts", "uniform sizing",
          "recycling pickup", "newsletter deadlines", "badge renewals", "van pool rosters",
          "locker assignments", "training calendars", "expense reporting", "supply reorders"]


def full_name(rng):
    return rng.choice(FIRST) + " " + rng.choice(LAST)


def safe_num(rng, lo, hi, dec, forbidden):
    for _ in range(200):
        v = round(rng.uniform(lo, hi), dec)
        if dec > 0 and abs(v - round(v)) < 10 ** (-dec) / 2:
            continue  # keep a nonzero fractional part for decimals
        if all(abs(v - f) > 1e-9 for f in forbidden):
            return v
    raise RuntimeError("could not draw safe number")


def distractor(rng, forbidden, used):
    n = lambda lo, hi: int(rng.uniform(lo, hi))
    d = lambda lo, hi, dec=1: safe_num(rng, lo, hi, dec, forbidden)
    T = [
        lambda: f"During the {rng.choice(SHIFTS)} shift on {rng.choice(DATES)}, {full_name(rng)} of the {rng.choice(TEAMS)} team walked the full inspection loop through {rng.choice(ROOMS)} in {n(18,95)} minutes, noting along the way that the {rng.choice(EQUIP)} had been serviced {n(3,40)} days earlier and that nothing unusual appeared in the sign-in ledger.",
        lambda: f"A routine memorandum circulated by {full_name(rng)} on {rng.choice(DATES)} reminded the {rng.choice(TEAMS)} group about {rng.choice(TOPICS)}, mentioned that {rng.choice(ROOMS)} would be repainted over the coming weekend, and asked staff to return any borrowed items from the {rng.choice(EQUIP)} station by the end of the month.",
        lambda: f"Weather observations logged at {n(6,11)}:{n(10,55):02d} that morning described {rng.choice(WEATHER)} over the site, with an ambient reading of {d(4,29)} degrees Celsius recorded near {rng.choice(ROOMS)}, none of which prompted any change to the posted work schedule maintained by the {rng.choice(TEAMS)} desk.",
        lambda: f"{full_name(rng)}, who has covered the {rng.choice(SHIFTS)} rotation for {n(2,14)} years, filed a short note stating that the {rng.choice(EQUIP)} near {rng.choice(ROOMS)} was making an intermittent clicking sound, and a work order numbered {n(40000,99999)} was opened with the {rng.choice(TEAMS)} queue to have it examined.",
        lambda: f"The staffing roster for {rng.choice(DATES)} showed {n(11,48)} personnel on site across three buildings, including {n(2,9)} temporary contractors assigned to the {rng.choice(TEAMS)} team, and the badge office confirmed that {full_name(rng)} had completed the annual escort refresher without any outstanding items.",
        lambda: f"An unrelated utility report noted that water consumption in {rng.choice(ROOMS)} ran at {d(120,940)} liters for the day, roughly in line with seasonal averages, and {full_name(rng)} of {rng.choice(TEAMS)} signed off on the meter reading after cross-checking it against the ledger kept beside the {rng.choice(EQUIP)}.",
        lambda: f"Minutes from the {rng.choice(SHIFTS)}-shift huddle on {rng.choice(DATES)} record a ten-minute discussion of {rng.choice(TOPICS)}, an agreement that {full_name(rng)} would draft the next rotation for the {rng.choice(TEAMS)} desk, and a reminder that the {rng.choice(EQUIP)} in {rng.choice(ROOMS)} should be powered down overnight.",
        lambda: f"The canteen invoice reconciled by {full_name(rng)} came to {d(180,2400)} in local currency for the week, covering {n(40,240)} meal vouchers, and the {rng.choice(TEAMS)} coordinator flagged nothing beyond a duplicated line item for the {rng.choice(EQUIP)} maintenance contract that was corrected the same afternoon.",
        lambda: f"A visitor delegation of {n(3,12)} arrived on {rng.choice(DATES)} for a tour of {rng.choice(ROOMS)}, escorted by {full_name(rng)}, and apart from a misplaced badge that was recovered near the {rng.choice(EQUIP)} within the hour, the {rng.choice(TEAMS)} log describes the visit as entirely uneventful.",
        lambda: f"Preventive maintenance ticket {n(40000,99999)} against the {rng.choice(EQUIP)} in {rng.choice(ROOMS)} was closed by {full_name(rng)} after {d(1.1,6.9)} labor hours, with the closing note stating that consumables were replaced from {rng.choice(TEAMS)} stock and no follow-up inspection was considered necessary.",
        lambda: f"The {rng.choice(TEAMS)} bulletin for {rng.choice(DATES)} devoted a paragraph to {rng.choice(TOPICS)}, thanked {full_name(rng)} for covering two consecutive {rng.choice(SHIFTS)} shifts, and noted that {n(4,28)} replacement lamps had been installed along the walkway outside {rng.choice(ROOMS)} without disrupting normal access.",
        lambda: f"Fleet records show the site's utility vehicle covered {d(14,240)} kilometers that week, mostly shuttling between {rng.choice(ROOMS)} and the perimeter gate, and {full_name(rng)} recorded that tire pressures were adjusted and the logbook countersigned by the {rng.choice(TEAMS)} supervisor on duty.",
        lambda: f"An email thread about {rng.choice(TOPICS)} that ran to {n(6,31)} replies was finally resolved when {full_name(rng)} agreed to host a short briefing in {rng.choice(ROOMS)} on {rng.choice(DATES)}, an outcome the {rng.choice(TEAMS)} lead described as overdue but welcome in the weekly summary.",
        lambda: f"Environmental services reported that {n(5,60)} kilograms of mixed recycling were collected from {rng.choice(ROOMS)} during the {rng.choice(SHIFTS)} shift, that the compactor beside the {rng.choice(EQUIP)} operated normally, and that {full_name(rng)} verified the manifest before the hauler departed at {n(13,18)}:{n(10,55):02d}.",
    ]
    for _ in range(80):
        s = rng.choice(T)()
        if s not in used:
            used.add(s)
            return s
    raise RuntimeError("distractor uniqueness exhausted")


WITNESS_T = [
    "The final verification sweep, countersigned by {name}, recorded the {p} at {v} {u}.",
    "Instrument logs attached to the closing review show that the {p} measured {v} {u}.",
    "According to the measurement annex compiled by {name}, the {p} came in at {v} {u}.",
    "The formally recorded reading for the {p}, entered into the decision file, was {v} {u}.",
]


def cond_clause(name, unit, direction, thr):
    word = "at most" if direction == "max" else "at least"
    t = int(thr) if float(thr) == int(thr) else thr
    return f"the {name} is {word} {t} {unit}"


def gen_items():
    rng = random.Random(42)
    patterns = [(True, True)] * 8 + [(True, False)] * 7 + [(False, True)] * 7 + [(False, False)] * 8
    rng.shuffle(patterns)
    codes = rng.sample([a + " " + b for a in ADJ for b in NOUN], 30)
    used_sentences = set()
    used_witness_vals = set()
    items = []
    for i, (approved, flip) in enumererate_safe(patterns):
        dom = DOMAINS[i % 6]
        drng = random.Random(1000 + i)
        params = drng.sample(dom["params"], 3)
        # thresholds
        conds = []
        forbidden = set()
        for (pname, unit, direction, lo, hi, dec) in params:
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)), 1)
            conds.append(dict(name=pname, unit=unit, dir=direction, thr=thr))
            forbidden.add(float(thr))
        # pass/fail pattern
        if approved:
            passing = [True, True, True]
        elif flip:
            passing = [True, True, True]
            passing[drng.randrange(3)] = False  # exactly one failing -> flippable
        else:
            nfail = drng.choice([1, 2, 3])
            idxs = drng.sample(range(3), nfail)
            passing = [j not in idxs for j in range(3)]
        # measured values
        for c, p in zip(conds, passing):
            span = max(abs(c["thr"]) * 0.3, 0.5)
            for _ in range(300):
                lo_v, hi_v =(c["thr"] - span, c["thr"] - 0.02 * span) if ((c["dir"] == "max") == p) else (c["thr"] + 0.02 * span, c["thr"] + span)
                v = round(drng.uniform(lo_v, hi_v), 2)
                if abs(v - round(v)) < 0.005:
                    continue
                ok_dir = (v <= c["thr"]) if c["dir"] == "max" else (v >= c["thr"])
                if ok_dir != p:
                    continue
                if v in used_witness_vals or any(abs(v - f) < 1e-9 for f in forbidden):
                    continue
                c["value"] = v
                c["passes"] = p
                used_witness_vals.add(v)
                forbidden.add(v)
                break
            else:
                raise RuntimeError("value draw failed")
        truth = "APPROVED" if all(c["passes"] for c in conds) else "DENIED"
        assert (truth == "APPROVED") == approved
        # counterfactual
        if approved and flip:
            j = drng.randrange(3)
            newpass = False
        elif approved and not flip:
            j = drng.randrange(3)
            newpass = True
        elif not approved and flip:
            j = passing.index(False)
            newpass = True
        else:
            j = passing.index(False)
            newpass = False
        c = conds[j]
        span = max(abs(c["thr"]) * 0.3, 0.5)
        for _ in range(300):
            lo_v, hi_v = (c["thr"] - span, c["thr"] - 0.02 * span) if ((c["dir"] == "max") == newpass) else (c["thr"] + 0.02 * span, c["thr"] + span)
            nv = round(drng.uniform(lo_v, hi_v), 2)
            if abs(nv - round(nv)) < 0.005 or abs(nv - c["value"]) < 1e-9:
                continue
            if any(abs(nv - f) < 1e-9 for f in forbidden):
                continue
            break
        else:
            raise RuntimeError("cf draw failed")
        forbidden.add(nv)
        cf_passing = list(passing)
        cf_passing[j] = newpass
        cf_truth = "APPROVED" if all(cf_passing) else "DENIED"
        assert (cf_truth != truth) == flip
        # document
        code = codes[i]
        event = dom["event"].format(code=code)
        policy = (f"INCIDENT REVIEW FILE — Operation {code}. This file concerns the go/no-go "
                  f"decision for {event}. POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
                  f"{cond_clause(conds[0]['name'], conds[0]['unit'], conds[0]['dir'], conds[0]['thr'])} AND "
                  f"{cond_clause(conds[1]['name'], conds[1]['unit'], conds[1]['dir'], conds[1]['thr'])} AND "
                  f"{cond_clause(conds[2]['name'], conds[2]['unit'], conds[2]['dir'], conds[2]['thr'])}; "
                  f"otherwise it is DENIED. The review board for Operation {code} asks that all "
                  f"supporting records remain attached to this file for audit purposes.")
        witness_sents = []
        for c in conds:
            for _ in range(40):
                t = drng.choice(WITNESS_T)
                s = t.format(name=full_name(drng), p=c["name"], v=c["value"], u=c["unit"])
                if s not in used_sentences:
                    used_sentences.add(s)
                    witness_sents.append(s)
                    break
            else:
                raise RuntimeError("witness uniqueness failed")
        body = []
        while True:
            body.append(distractor(drng, forbidden, used_sentences))
            wc = len(policy.split()) + sum(len(s.split()) for s in body) + sum(len(s.split()) for s in witness_sents)
            if wc >= 1420 and len(body) >= 26:
                break
            if len(body) > 45:
                break
        positions = sorted(drng.sample(range(len(body) + 1), 3))
        for off, (pos, ws) in enumerate(zip(positions, witness_sents)):
            body.insert(pos + off, ws)
        paras, k = [], 0
        while k < len(body):
            step = drng.choice([4, 5, 6])
            paras.append(" ".join(body[k:k + step]))
            k += step
        doc = policy + "\n\n" + "\n\n".join(paras) + "\n\nEnd of file."
        items.append(dict(
            id=f"item{i:02d}", domain=dom["domain"], code=code, event=event, truth=truth,
            conditions=[dict(name=c["name"], unit=c["unit"], dir=c["dir"], thr=c["thr"],
                             value=c["value"], passes=c["passes"]) for c in conds],
            cf_param=conds[j]["name"], cf_unit=conds[j]["unit"], cf_value=nv,
            cf_truth=cf_truth, cf_flips=flip, word_count=len(doc.split()), document=doc))
    return items


def enumererate_safe(x):
    return enumerate(x)

# ---------------------------------------------------------------- API

USAGE = {"prompt": 0, "completion": 0, "total": 0}


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        with open(RAW) as f:
            for line in f:
                r = json.loads(line)
                cache[(r["item"], r["call"], r["wl"])] = r
    return cache


def api(messages, cache, key_fn, meta):
    if key_fn in cache:
        return cache[key_fn]["text"]
    made = sum(1 for k in cache if True)
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
            code = e.code
            detail = e.read()[:300].decode(errors="replace")
            if code in (429,) or code >= 500:
                if attempt == 2:
                    raise RuntimeError(f"API failed after retries: {code} {detail}")
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"API error {code}: {detail}")
        except urllib.error.URLError as e:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))
    text = data["choices"][0]["message"]["content"]
    u = data.get("usage", {})
    rec = dict(item=key_fn[0], call=key_fn[1], wl=key_fn[2], text=text,
               usage=dict(prompt=u.get("prompt_tokens", 0), completion=u.get("completion_tokens", 0),
                          total=u.get("total_tokens", 0)), **meta)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key_fn] = rec
    return text


ANS_SUFFIX = ("Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED|DENIED, "
              "then EVIDENCE: and quote or paraphrase the specific facts (with numbers) that determine it.")


def run_items(items, start, end, wl):
    cache = load_cache()
    for it in items[start:end]:
        iid = it["id"]
        comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                    f"following file to at most {wl} words, preserving whatever a future analyst will "
                    f"need to answer questions about the go/no-go decision. Output only the compressed notes.")
        summary = api([{"role": "system", "content": comp_sys},
                       {"role": "user", "content": it["document"]}],
                      cache, (iid, "compress", wl), {})
        api([{"role": "user", "content": it["document"] + "\n\n" + ANS_SUFFIX}],
            cache, (iid, "answer_full", 0), {})
        api([{"role": "user", "content": "Compressed case notes:\n" + summary + "\n\n" + ANS_SUFFIX}],
            cache, (iid, "answer_comp", wl), {})
        tcf = it["cf_value"]
        cfv = f"{tcf} {it['cf_unit']}"
        api([{"role": "user", "content": ("Compressed case notes:\n" + summary +
             f"\n\nCounterfactual: suppose instead the {it['cf_param']} had been {cfv}. Per the policy, "
             "would the decision be APPROVED or DENIED? Reply exactly: ANSWER: APPROVED|DENIED.")}],
            cache, (iid, "cf_comp", wl), {})
        api([{"role": "user", "content": ("Compressed case notes:\n" + summary + "\n\n" + ANS_SUFFIX +
             " If the notes do not contain enough information to determine the decision per policy, "
             "reply exactly: ANSWER: INSUFFICIENT_EVIDENCE.")}],
            cache, (iid, "abstain_comp", wl), {})
        print(f"{iid} done ({len(cache)} calls cached)")

# ---------------------------------------------------------------- scoring

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
ANS_RE = re.compile(r"ANSWER:?\s*\**\s*(APPROVED|DENIED|INSUFFICIENT[_ ]EVIDENCE)", re.I)


def numbers(text):
    return [float(m) for m in NUM_RE.findall(text.replace(",", ""))]


def has_value(text, v):
    return any(abs(x - v) < 1e-9 for x in numbers(text))


def parse_answer(text):
    m = ANS_RE.search(text)
    if not m:
        return None
    a = m.group(1).upper().replace(" ", "_")
    return a


def evidence_of(text):
    parts = re.split(r"EVIDENCE:?", text, flags=re.I)
    return parts[1] if len(parts) > 1 else text


def witness_frac(text, item):
    return sum(1 for c in item["conditions"] if has_value(text, c["value"])) / 3.0


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
            full = g("answer_full", 0)
            comp = g("answer_comp", wl)
            cf = g("cf_comp", wl)
            ab = g("abstain_comp", wl)
            row = dict(item=iid, domain=it["domain"], truth=it["truth"], cf_truth=it["cf_truth"],
                       cf_flips=it["cf_flips"], summary_words=len(summary.split()))
            row["retention"] = witness_frac(summary, it)
            for name, txt, wf in [("full", full, True), ("comp", comp, True),
                                  ("cf", cf, False), ("ab", ab, False)]:
                a = parse_answer(txt) if txt else None
                if txt and a is None:
                    anomalies.append((iid, name, txt[:160]))
                row[name + "_answer"] = a
                if wf:
                    row[name + "_witness"] = witness_frac(evidence_of(txt), it) if txt else None
            row["full_correct"] = row["full_answer"] == it["truth"]
            row["comp_correct"] = row["comp_answer"] == it["truth"]
            row["cf_correct"] = row["cf_answer"] == it["cf_truth"]
            row["abstained"] = row["ab_answer"] == "INSUFFICIENT_EVIDENCE"
            row["ab_correct"] = row["ab_answer"] == it["truth"]
            if row["comp_correct"] and row["comp_witness"] == 1.0:
                row["cls"] = "justified"
            elif row["comp_correct"]:
                row["cls"] = "debt"
            else:
                row["cls"] = "wrong"
            rows.append(row)
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    print(f"\n=== REPORT (n={n}, compression limit {wl} words) ===")
    print(f"answer accuracy   full={mean([r['full_correct'] for r in rows]):.3f}  comp={mean([r['comp_correct'] for r in rows]):.3f}")
    print(f"witness fidelity  full={mean([r['full_witness'] for r in rows]):.3f}  comp={mean([r['comp_witness'] for r in rows]):.3f}")
    print(f"summary retention {mean([r['retention'] for r in rows]):.3f}   mean summary words {mean([r['summary_words'] for r in rows]):.1f}")
    for cls in ("justified", "debt", "wrong"):
        sub = [r for r in rows if r["cls"] == cls]
        if sub:
            print(f"CF acc | {cls:9s}: {sum(r['cf_correct'] for r in sub)}/{len(sub)} = {mean([r['cf_correct'] for r in sub]):.3f}"
                  f"   (flip items: {sum(r['cf_flips'] for r in sub)})")
    print(f"CF acc overall: {mean([r['cf_correct'] for r in rows]):.3f}")
    print(f"abstentions: {sum(r['abstained'] for r in rows)}")
    for cls in ("justified", "debt", "wrong"):
        sub = [r for r in rows if r["cls"] == cls]
        if sub:
            print(f"  abstain | {cls:9s}: {sum(r['abstained'] for r in sub)}/{len(sub)}")
    print(f"tokens: prompt={tok['prompt']} completion={tok['completion']} total={tok['total']}")
    print(f"anomalies (unparseable): {len(anomalies)}")
    for a in anomalies:
        print("  ", a)
    debt_ex = [r for r in rows if r["cls"] == "debt"][:3]
    for r in debt_ex:
        txt = cache[(r["item"], "answer_comp", wl)]["text"]
        print(f"\n--- debt example {r['item']} (truth {r['truth']}, cf_correct={r['cf_correct']}) ---")
        print(txt[:600])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "run", "score"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=30)
    ap.add_argument("--wl", type=int, default=120)
    a = ap.parse_args()
    if a.cmd == "gen":
        items = gen_items()
        with open(ITEMS, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        wcs = [it["word_count"] for it in items]
        print(f"generated {len(items)} items; words min={min(wcs)} max={max(wcs)} "
              f"approved={sum(it['truth']=='APPROVED' for it in items)} "
              f"flips={sum(it['cf_flips'] for it in items)}")
        return
    items = [json.loads(l) for l in open(ITEMS)]
    if a.cmd == "run":
        run_items(items, a.start, a.end, a.wl)
    else:
        score(items, a.wl)


if __name__ == "__main__":
    main()
