#!/usr/bin/env python3
"""v2 pilot: contract-blind compaction. Doc has 12 unmarked numeric parameters (3 secretly
policy-relevant); compressor never sees the policy; policy revealed only at answer time.

Subcommands:
  gen                         generate items.jsonl (seeded, no LLM)
  run --start A --end B --wl W    run 5 calls per item with compression word limit W
  score --wl W                score, write summaries.jsonl / scored.csv, print report
"""
import argparse, csv, json, os, random, re, sys, time
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(HERE, "..", "..", "secrets", "xai_key")
ITEMS = os.path.join(HERE, "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
SUMS = os.path.join(HERE, "summaries.jsonl")
SCORED = os.path.join(HERE, "scored.csv")
MODEL = "grok-4-1-fast-non-reasoning"
URL = "https://api.x.ai/v1/chat/completions"
HARD_CAP = 400

# ---------------------------------------------------------------- pools

# (name, unit, policy_dir, lo, hi, dec) — policy_dir used only if chosen as policy param
DOMAINS = [
    dict(domain="satellite launch", event="the launch of the {code} payload", params=[
        ("sensor calibration offset", "mrad", "max", 0.3, 0.9, 2),
        ("backup battery charge", "percent", "min", 70, 92, 1),
        ("lead operator certification rating", "points", "min", 3.0, 4.5, 1),
        ("guidance regression pass rate", "percent", "min", 92, 99, 1),
        ("fairing pressure differential", "kPa", "max", 2.0, 6.0, 1),
        ("telemetry downlink margin", "dB", "min", 3, 12, 1),
        ("propellant tank ullage pressure", "bar", "max", 4, 9, 1),
        ("gyro drift rate", "degrees per hour", "max", 0.1, 0.8, 2),
        ("pad ambient wind speed", "m/s", "max", 4, 14, 1),
        ("umbilical retract time", "seconds", "max", 2, 8, 1),
        ("star tracker residual", "arcseconds", "max", 10, 40, 1),
        ("RF noise margin", "dB", "min", 2, 10, 1),
        ("avionics bus load", "percent", "max", 40, 80, 1),
        ("thermal blanket coverage", "percent", "min", 88, 99, 1)]),
    dict(domain="chemical batch release", event="release of the {code} production batch", params=[
        ("residual solvent concentration", "ppm", "max", 40, 120, 1),
        ("batch purity assay", "percent", "min", 95, 99, 1),
        ("cooling loop flow rate", "L/min", "min", 30, 80, 1),
        ("catalyst moisture content", "percent", "max", 1.0, 4.0, 1),
        ("QA composite audit score", "points", "min", 80, 95, 1),
        ("reactor jacket temperature", "degrees Celsius", "max", 60, 110, 1),
        ("agitator torque", "N-m", "max", 120, 300, 1),
        ("filtrate turbidity", "NTU", "max", 2, 12, 1),
        ("nitrogen blanket pressure", "kPa", "min", 15, 40, 1),
        ("particulate count index", "points", "max", 50, 150, 1),
        ("yield efficiency", "percent", "min", 70, 95, 1),
        ("condenser outlet temperature", "degrees Celsius", "max", 20, 45, 1),
        ("seal integrity margin", "percent", "min", 80, 98, 1),
        ("discharge line conductivity", "microsiemens", "max", 20, 90, 1)]),
    dict(domain="rail switch deployment", event="deployment of the {code} switch assembly", params=[
        ("actuator response latency", "ms", "max", 120, 400, 1),
        ("track gauge deviation", "mm", "max", 1.5, 5.0, 1),
        ("interlock relay voltage", "volts", "min", 22, 26, 1),
        ("ballast compaction index", "points", "min", 60, 90, 1),
        ("signal alignment error", "degrees", "max", 0.4, 1.6, 2),
        ("point blade wear", "mm", "max", 2, 9, 1),
        ("drive motor current draw", "amperes", "max", 8, 25, 1),
        ("heater circuit resistance", "ohms", "min", 10, 30, 1),
        ("detection loop sensitivity", "percent", "min", 75, 95, 1),
        ("lubrication film thickness", "microns", "min", 20, 80, 1),
        ("sleeper spacing variance", "mm", "max", 3, 12, 1),
        ("crossing angle tolerance", "degrees", "max", 0.5, 2.0, 2),
        ("cable insulation resistance", "megohms", "min", 5, 40, 1),
        ("switch throw force", "kN", "max", 2, 7, 2)]),
    dict(domain="data-center failover", event="the {code} failover cutover", params=[
        ("replication lag", "seconds", "max", 4, 18, 1),
        ("UPS reserve charge", "percent", "min", 65, 90, 1),
        ("standby CPU headroom", "percent", "min", 25, 55, 1),
        ("packet loss on the interconnect", "percent", "max", 0.5, 2.5, 2),
        ("generator fuel reserve", "hours", "min", 8, 24, 1),
        ("chilled water supply temperature", "degrees Celsius", "max", 7, 16, 1),
        ("rack inlet temperature", "degrees Celsius", "max", 18, 30, 1),
        ("storage array rebuild margin", "percent", "min", 20, 60, 1),
        ("DNS failover propagation time", "seconds", "max", 20, 90, 1),
        ("battery string impedance", "milliohms", "max", 20, 60, 1),
        ("cold aisle humidity", "percent", "min", 30, 55, 1),
        ("transfer switch actuation time", "ms", "max", 80, 300, 1),
        ("standby link utilization", "percent", "max", 30, 70, 1),
        ("disk queue depth index", "points", "max", 10, 40, 1)]),
    dict(domain="vaccine lot release", event="release of the {code} vaccine lot", params=[
        ("cumulative cold-chain excursion", "minutes", "max", 20, 90, 1),
        ("potency assay result", "percent of label claim", "min", 90, 105, 1),
        ("endotoxin level", "EU/mL", "max", 0.5, 2.0, 2),
        ("fill-volume deviation", "percent", "max", 1.0, 3.5, 2),
        ("stability composite score", "points", "min", 75, 95, 1),
        ("sterility clarity index", "points", "min", 70, 95, 1),
        ("vial headspace oxygen", "percent", "max", 1, 5, 2),
        ("adjuvant concentration ratio", "percent", "min", 90, 105, 1),
        ("lyophilization residual moisture", "percent", "max", 1, 3, 2),
        ("particulate burden index", "points", "max", 20, 80, 1),
        ("label reconciliation rate", "percent", "min", 97, 99.9, 2),
        ("freezer alarm response time", "minutes", "max", 5, 25, 1),
        ("seal torque retention", "percent", "min", 80, 95, 1),
        ("diluent conductivity", "microsiemens", "max", 5, 30, 1)]),
    dict(domain="bridge load test", event="certification of the {code} span load test", params=[
        ("peak midspan deflection", "mm", "max", 20, 60, 1),
        ("anchor bolt torque", "N-m", "min", 300, 500, 1),
        ("concrete core strength", "MPa", "min", 30, 55, 1),
        ("vibration amplitude", "mm/s", "max", 3.0, 9.0, 2),
        ("bearing seat rotation", "degrees", "max", 0.5, 1.8, 2),
        ("expansion joint gap", "mm", "min", 20, 60, 1),
        ("cable tension uniformity", "percent", "min", 85, 98, 1),
        ("pier settlement reading", "mm", "max", 2, 10, 2),
        ("deck temperature differential", "degrees Celsius", "max", 5, 18, 1),
        ("maximum crack width", "mm", "max", 0.1, 0.6, 2),
        ("load distribution factor", "points", "min", 60, 90, 1),
        ("rebar cover depth", "mm", "min", 30, 70, 1),
        ("grout compressive margin", "percent", "min", 75, 95, 1),
        ("gust speed during test", "m/s", "max", 5, 18, 1)]),
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
MONTHS = ["early March", "mid-March", "late March", "early April", "mid-April", "late April",
          "early May", "mid-May", "late May", "early June", "mid-June", "late June"]
EQUIP = ["forklift", "badge scanner", "HVAC chiller", "spare parts cabinet", "loading dock crane",
         "coffee dispenser", "intercom console", "shredder", "label printer", "pallet wrapper",
         "service elevator", "floor scrubber", "conference projector", "keycard encoder",
         "backup printer", "air compressor", "utility cart", "document scanner"]
ROOMS = ["annex B", "the west mezzanine", "corridor seven", "the staging bay", "dock three",
         "the records vault", "hangar two", "the north stairwell", "briefing room four",
         "the equipment cage", "sublevel one", "the visitor lobby"]
TOPICS = ["parking allocation", "cafeteria menus", "visitor escorts", "uniform sizing",
          "recycling pickup", "newsletter deadlines", "badge renewals", "van pool rosters",
          "locker assignments", "training calendars", "expense reporting", "supply reorders"]


def full_name(rng):
    return rng.choice(FIRST) + " " + rng.choice(LAST)


def nn_distractor(rng, used):
    T = [
        lambda: f"During the {rng.choice(SHIFTS)} shift in {rng.choice(MONTHS)}, {full_name(rng)} of the {rng.choice(TEAMS)} team walked the inspection loop through {rng.choice(ROOMS)}, noting that the {rng.choice(EQUIP)} had been serviced earlier that week and that nothing unusual appeared in the sign-in ledger.",
        lambda: f"A routine memorandum circulated by {full_name(rng)} reminded the {rng.choice(TEAMS)} group about {rng.choice(TOPICS)}, mentioned that {rng.choice(ROOMS)} would be repainted over the coming weekend, and asked staff to return any items borrowed from the {rng.choice(EQUIP)} station.",
        lambda: f"{full_name(rng)}, who has covered the {rng.choice(SHIFTS)} rotation for several years, filed a short note stating that the {rng.choice(EQUIP)} near {rng.choice(ROOMS)} was making an intermittent clicking sound, and a work order was opened with the {rng.choice(TEAMS)} queue.",
        lambda: f"Minutes from the {rng.choice(SHIFTS)}-shift huddle in {rng.choice(MONTHS)} record a brief discussion of {rng.choice(TOPICS)}, an agreement that {full_name(rng)} would draft the next rotation for the {rng.choice(TEAMS)} desk, and a reminder to power down the {rng.choice(EQUIP)} overnight.",
        lambda: f"A small visitor delegation toured {rng.choice(ROOMS)} in {rng.choice(MONTHS)}, escorted by {full_name(rng)}, and apart from a misplaced badge recovered near the {rng.choice(EQUIP)} within the hour, the {rng.choice(TEAMS)} log describes the visit as entirely uneventful.",
        lambda: f"The {rng.choice(TEAMS)} bulletin devoted a paragraph to {rng.choice(TOPICS)}, thanked {full_name(rng)} for covering consecutive {rng.choice(SHIFTS)} shifts, and noted that replacement lamps had been installed along the walkway outside {rng.choice(ROOMS)} without disrupting access.",
        lambda: f"An email thread about {rng.choice(TOPICS)} was finally resolved when {full_name(rng)} agreed to host a short briefing in {rng.choice(ROOMS)}, an outcome the {rng.choice(TEAMS)} lead described in the weekly summary as overdue but welcome.",
        lambda: f"Environmental services reported that mixed recycling was collected from {rng.choice(ROOMS)} during the {rng.choice(SHIFTS)} shift, that the compactor beside the {rng.choice(EQUIP)} operated normally, and that {full_name(rng)} verified the manifest before the hauler departed.",
        lambda: f"Weather over the site in {rng.choice(MONTHS)} was unremarkable, and {full_name(rng)} of the {rng.choice(TEAMS)} desk confirmed that the posted work schedule for {rng.choice(ROOMS)} required no changes beyond swapping a pair of {rng.choice(SHIFTS)}-shift assignments.",
        lambda: f"Preventive maintenance on the {rng.choice(EQUIP)} in {rng.choice(ROOMS)} was closed out by {full_name(rng)}, with the note stating that consumables were replaced from {rng.choice(TEAMS)} stock and that no follow-up inspection was considered necessary.",
        lambda: f"The badge office confirmed that {full_name(rng)} completed the annual escort refresher without outstanding items, and the {rng.choice(TEAMS)} coordinator updated the roster kept beside the {rng.choice(EQUIP)} in {rng.choice(ROOMS)} accordingly.",
        lambda: f"A duplicated line item in the {rng.choice(TEAMS)} ledger concerning the {rng.choice(EQUIP)} maintenance contract was corrected the same afternoon it was flagged, and {full_name(rng)} countersigned the amended page during the {rng.choice(SHIFTS)} shift.",
    ]
    for _ in range(120):
        s = rng.choice(T)()
        if s not in used:
            used.add(s)
            return s
    raise RuntimeError("distractor uniqueness exhausted")


PARAM_T = [
    "The {p} was recorded at {v} {u} by {name} during the review.",
    "Instrument logs attached to the file show the {p} at {v} {u}.",
    "According to the measurement annex compiled by {name}, the {p} came in at {v} {u}.",
    "The formally entered reading for the {p} was {v} {u}.",
    "The closing sweep, countersigned by {name}, put the {p} at {v} {u}.",
    "The duty recorder logged the {p} as {v} {u}.",
]


def cond_clause(name, unit, direction, thr):
    word = "at most" if direction == "max" else "at least"
    t = int(thr) if float(thr) == int(thr) else thr
    return f"the {name} is {word} {t} {unit}"


def draw_value(rng, thr, direction, want_pass, span, forbidden):
    for _ in range(400):
        lo_v, hi_v = (thr - span, thr - 0.02 * span) if ((direction == "max") == want_pass) \
            else (thr + 0.02 * span, thr + span)
        v = round(rng.uniform(lo_v, hi_v), 2)
        if abs(v - round(v)) < 0.005:
            continue
        ok = (v <= thr) if direction == "max" else (v >= thr)
        if ok != want_pass:
            continue
        if any(abs(v - f) < 1e-9 for f in forbidden):
            continue
        return v
    raise RuntimeError("value draw failed")


def gen_items():
    rng = random.Random(4242)
    # (approved, nfail, flip): 30 approved (20 flip / 10 noflip);
    # 30 denied: 10 x 1-fail (flip), 10 x 2-fail (noflip), 10 x 3-fail (noflip)
    patterns = ([(True, 0, True)] * 20 + [(True, 0, False)] * 10 +
                [(False, 1, True)] * 10 + [(False, 2, False)] * 10 + [(False, 3, False)] * 10)
    rng.shuffle(patterns)
    codes = rng.sample([a + " " + b for a in ADJ for b in NOUN], 60)
    used_sentences, items = set(), []
    for i, (approved, nfail, flip) in enumerate(patterns):
        dom = DOMAINS[i % 6]
        drng = random.Random(5000 + i)
        chosen = drng.sample(dom["params"], 12)
        pol_idx = sorted(drng.sample(range(12), 3))
        forbidden = set()
        plist = []
        # policy params first: thresholds + pass/fail assignment
        fail_slots = set(drng.sample(range(3), nfail))
        for k, pi in enumerate(pol_idx):
            name, unit, direction, lo, hi, dec = chosen[pi]
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)), 1)
            forbidden.add(float(thr))
            span = max(abs(thr) * 0.3, 0.5)
            p = k not in fail_slots
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
        # counterfactual on a policy param
        if approved:
            j = drng.randrange(3)
            newpass = not flip
        else:
            failing = [k for k, d in enumerate(pol) if not d["passes"]]
            j = drng.choice(failing)
            newpass = flip  # flip only when nfail==1
        c = pol[j]
        span = max(abs(c["thr"]) * 0.3, 0.5)
        nv = draw_value(drng, c["thr"], c["dir"], newpass, span, forbidden | {c["value"]})
        forbidden.add(nv)
        cf_pass = [d["passes"] for d in pol]
        cf_pass[j] = newpass
        cf_truth = "APPROVED" if all(cf_pass) else "DENIED"
        assert (cf_truth != truth) == flip
        # document (NO policy)
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
            id=f"v2item{i:02d}", domain=dom["domain"], code=code, event=event, truth=truth,
            nfail=nfail, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            cf_param=c["name"], cf_unit=c["unit"], cf_value=nv, cf_truth=cf_truth,
            cf_flips=flip, word_count=len(doc.split()), document=doc))
    return items

# ---------------------------------------------------------------- API (same as v1)


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


def run_items(items, start, end, wl):
    cache = load_cache()
    for it in items[start:end]:
        iid = it["id"]
        comp_sys = (f"You are a context compaction engine for an operations assistant. Compress the "
                    f"following incident file to at most {wl} words. A future analyst will need to "
                    f"answer questions about this incident, but you do not know which questions. "
                    f"Output only the compressed notes.")
        summary = api([{"role": "system", "content": comp_sys},
                       {"role": "user", "content": it["document"]}], cache, (iid, "compress", wl))
        pol = it["policy_text"]
        api([{"role": "user", "content": pol + "\n\n" + it["document"] + "\n\n" + ANS_SUFFIX}],
            cache, (iid, "answer_full", 0))
        api([{"role": "user", "content": pol + "\n\nCompressed case notes:\n" + summary +
              "\n\n" + ANS_SUFFIX}], cache, (iid, "answer_comp", wl))
        api([{"role": "user", "content": (pol + "\n\nCompressed case notes:\n" + summary +
              f"\n\nCounterfactual: suppose instead the {it['cf_param']} had been "
              f"{it['cf_value']} {it['cf_unit']}. Per the policy, would the decision be APPROVED "
              "or DENIED? Reply exactly: ANSWER: APPROVED|DENIED.")}], cache, (iid, "cf_comp", wl))
        api([{"role": "user", "content": (pol + "\n\nCompressed case notes:\n" + summary +
              "\n\n" + ANS_SUFFIX +
              " If the notes do not contain enough information to determine the decision per "
              "policy, reply exactly: ANSWER: INSUFFICIENT_EVIDENCE.")}],
            cache, (iid, "abstain_comp", wl))
        print(f"{iid} done ({len(cache)} calls cached)", flush=True)

# ---------------------------------------------------------------- scoring

NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")
ANS_RE = re.compile(r"ANSWER:?\s*\**\s*(APPROVED|DENIED|INSUFFICIENT[_ ]EVIDENCE)", re.I)
GIST_RE = re.compile(r"anomal|exceed|below|out[- ]of[- ]spec|out of range|marginal|elevated|"
                     r"degraded|warning|abnormal|deviat|breach|violat|fail|flag|too (high|low)|"
                     r"noncompliant|non-compliant", re.I)


def numbers(text):
    return [float(m) for m in NUM_RE.findall(text.replace(",", ""))]


def has_value(text, v):
    return any(abs(x - v) < 1e-9 for x in numbers(text))


def parse_answer(text):
    m = ANS_RE.search(text)
    return m.group(1).upper().replace(" ", "_") if m else None


def evidence_of(text):
    parts = re.split(r"EVIDENCE:?", text, flags=re.I)
    return parts[1] if len(parts) > 1 else text


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
            nonpol = [p for p in it["parameters"] if not p["policy"]]
            ret_pol = [has_value(summary, p["value"]) for p in pol]
            ret_non = [has_value(summary, p["value"]) for p in nonpol]
            row = dict(item=iid, domain=it["domain"], truth=it["truth"], nfail=it["nfail"],
                       cf_truth=it["cf_truth"], cf_flips=it["cf_flips"],
                       summary_words=len(summary.split()),
                       ret_policy=sum(ret_pol) / 3, ret_nonpolicy=sum(ret_non) / 9,
                       lost_any_policy=not all(ret_pol))
            cfp = next(p for p in pol if p["name"] == it["cf_param"])
            row["cf_param_retained"] = has_value(summary, cfp["value"])
            # determinable: APPROVED needs all 3; DENIED needs >=1 failing value retained
            if it["truth"] == "APPROVED":
                row["determinable"] = all(ret_pol)
            else:
                row["determinable"] = any(r for r, p in zip(ret_pol, pol) if not p["passes"])
            row["gist_leak"] = bool(GIST_RE.search(summary)) and row["lost_any_policy"]
            for name in ("answer_full", "answer_comp", "cf_comp", "abstain_comp"):
                w = 0 if name == "answer_full" else wl
                txt = g(name, w)
                a = parse_answer(txt) if txt else None
                if txt and a is None:
                    anomalies.append((iid, name, txt[:160]))
                row[name] = a
            row["full_witness"] = (sum(has_value(evidence_of(g("answer_full", 0) or ""), p["value"])
                                       for p in pol) / 3)
            row["comp_witness"] = (sum(has_value(evidence_of(g("answer_comp", wl) or ""), p["value"])
                                       for p in pol) / 3)
            row["full_correct"] = row["answer_full"] == it["truth"]
            row["comp_correct"] = row["answer_comp"] == it["truth"]
            row["cf_correct"] = row["cf_comp"] == it["cf_truth"]
            row["abstained"] = row["abstain_comp"] == "INSUFFICIENT_EVIDENCE"
            row["debt"] = row["comp_correct"] and row["lost_any_policy"]
            row["confabulated"] = (not row["determinable"]) and not row["abstained"] \
                and row["abstain_comp"] in ("APPROVED", "DENIED")
            rows.append(row)
    with open(SCORED, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")
    pct = lambda xs: f"{mean(xs):.3f}"
    print(f"\n=== v2 REPORT (n={n}, compression limit {wl} words) ===")
    print("P1  full acc={} comp acc={} | full witness={} comp witness={}".format(
        pct([r["full_correct"] for r in rows]), pct([r["comp_correct"] for r in rows]),
        pct([r["full_witness"] for r in rows]), pct([r["comp_witness"] for r in rows])))
    print("    summary retention: policy params={} nonpolicy params={} (mean words {:.1f})".format(
        pct([r["ret_policy"] for r in rows]), pct([r["ret_nonpolicy"] for r in rows]),
        mean([r["summary_words"] for r in rows])))
    for t in ("APPROVED", "DENIED"):
        sub = [r for r in rows if r["truth"] == t]
        print(f"    comp acc | {t}: {sum(r['comp_correct'] for r in sub)}/{len(sub)}"
              f"  (full: {sum(r['full_correct'] for r in sub)}/{len(sub)})")
    for nf in (1, 2, 3):
        sub = [r for r in rows if r["truth"] == "DENIED" and r["nfail"] == nf]
        if sub:
            print(f"      DENIED nfail={nf}: comp acc {sum(r['comp_correct'] for r in sub)}/{len(sub)}"
                  f", policy retention {pct([r['ret_policy'] for r in sub])}")
    print("P2  CF accuracy conditional on summary retaining the CF parameter value:")
    for cond, lab in ((True, "retained"), (False, "lost    ")):
        sub = [r for r in rows if r["cf_param_retained"] == cond]
        if sub:
            print(f"      {lab}: {sum(r['cf_correct'] for r in sub)}/{len(sub)} = "
                  f"{pct([r['cf_correct'] for r in sub])} (flip items {sum(r['cf_flips'] for r in sub)})")
    print(f"      overall: {pct([r['cf_correct'] for r in rows])}")
    for cls, pred in (("justified", lambda r: r["comp_correct"] and not r["lost_any_policy"]),
                      ("debt", lambda r: r["debt"]),
                      ("wrong", lambda r: not r["comp_correct"])):
        sub = [r for r in rows if pred(r)]
        if sub:
            print(f"      CF acc | {cls:9s}: {sum(r['cf_correct'] for r in sub)}/{len(sub)}")
    print(f"P3  abstentions: {sum(r['abstained'] for r in rows)}/{n}")
    for cond, lab in ((True, "lost>=1 policy value"), (False, "all policy retained ")):
        sub = [r for r in rows if r["lost_any_policy"] == cond]
        if sub:
            print(f"      abstain | {lab}: {sum(r['abstained'] for r in sub)}/{len(sub)}")
    nd = [r for r in rows if not r["determinable"]]
    print(f"    not-determinable-from-summary items: {len(nd)}; "
          f"confabulation rate (abstain call answered anyway): "
          f"{sum(r['confabulated'] for r in nd)}/{len(nd)}" if nd else "    all items determinable")
    print(f"    gist leakage (qualitative flag + lost value): {sum(r['gist_leak'] for r in rows)}/{n}")
    print(f"tokens: prompt={tok['prompt']} completion={tok['completion']} total={tok['total']}")
    print(f"anomalies (unparseable): {len(anomalies)}")
    for a in anomalies:
        print("  ", a)
    lost = [r for r in rows if r["lost_any_policy"]][:3]
    for r in lost:
        print(f"\n--- lost-witness summary {r['item']} (truth {r['truth']}, comp_correct="
              f"{r['comp_correct']}, cf_retained={r['cf_param_retained']}) ---")
        print(cache[(r["item"], "compress", wl)]["text"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "run", "score"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=60)
    ap.add_argument("--wl", type=int, default=60)
    a = ap.parse_args()
    if a.cmd == "gen":
        items = gen_items()
        with open(ITEMS, "w") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        wcs = [it["word_count"] for it in items]
        print(f"generated {len(items)} items; words min={min(wcs)} max={max(wcs)} "
              f"approved={sum(it['truth'] == 'APPROVED' for it in items)} "
              f"flips={sum(it['cf_flips'] for it in items)} "
              f"nfail dist={[sum(it['nfail'] == k for it in items) for k in (0, 1, 2, 3)]}")
        return
    items = [json.loads(l) for l in open(ITEMS)]
    if a.cmd == "run":
        run_items(items, a.start, a.end, a.wl)
    else:
        score(items, a.wl)


if __name__ == "__main__":
    main()
