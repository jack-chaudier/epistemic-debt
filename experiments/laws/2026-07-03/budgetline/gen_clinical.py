#!/usr/bin/env python3
"""Fresh domain for Phase 1: clinical trial enrollment eligibility.

Patient charts (~750 words) with 12 numeric labs/vitals, 3 of them secretly
eligibility-relevant, embedded among number-free clinical-narrative distractors.
Policy = conjunction of 3 threshold criteria; verdict APPROVED (enroll) / DENIED
(exclude). Same item schema as the v5 incident corpus so all v3 scoring machinery
(retained / parse_which / match_param / ANS_RE) applies unchanged.

Confound guards (v2-v5 checklist):
  - salience: policy and non-policy labs share the same sentence templates, shuffled.
  - verdict leak: the chart never states eligibility, thresholds, or spec language.
  - metric confound: all 12 values pairwise distinct, non-round; policy thresholds
    excluded from non-policy draws so retained() cannot false-match.
Stdlib only, seeded, no LLM. Writes items.jsonl next to this file.
"""
import json, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROK_PILOTS = os.path.join(HERE, "..", "..", "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK_PILOTS, "v2"))
sys.path.insert(0, os.path.join(GROK_PILOTS, "v3"))
from runner2 import cond_clause, draw_value  # reuse exact threshold/value logic
from runner3 import retained, match_param    # metric functions; used in draw + self-check


def collides(v, forbidden):
    """True if v would be confused with any already-placed value by retained()."""
    return any(retained(f"{v}", f) or retained(f"{f}", v) for f in forbidden)

ITEMS = os.path.join(HERE, "items_clinical.jsonl")

# 6 trial protocols; each has 14 candidate labs/vitals (name, unit, dir, lo, hi, dec).
# Numbers chosen so the 12 sampled per item stay in plausible clinical ranges.
PROTOCOLS = [
    dict(domain="oncology phase-II", event="enrollment of participant {code} in the {code} oncology cohort", params=[
        ("absolute neutrophil count", "cells per microliter", "min", 1500, 4200, 0),
        ("platelet count", "thousand per microliter", "min", 100, 320, 0),
        ("creatinine clearance", "milliliters per minute", "min", 45, 110, 0),
        ("total bilirubin", "milligrams per deciliter", "max", 0.6, 1.8, 1),
        ("left ventricular ejection fraction", "percent", "min", 50, 68, 0),
        ("ECOG performance score", "points", "max", 0, 2, 0),
        ("hemoglobin", "grams per deciliter", "min", 9.0, 14.5, 1),
        ("alanine aminotransferase", "units per liter", "max", 20, 70, 0),
        ("serum albumin", "grams per deciliter", "min", 3.0, 4.6, 1),
        ("corrected QT interval", "milliseconds", "max", 400, 470, 0),
        ("fasting glucose", "milligrams per deciliter", "max", 85, 135, 0),
        ("body mass index", "kilograms per square meter", "min", 18.5, 31, 1),
        ("systolic blood pressure", "millimeters of mercury", "max", 118, 158, 0),
        ("white blood cell count", "thousand per microliter", "min", 3.0, 9.5, 1)]),
    dict(domain="cardiology device", event="enrollment of participant {code} in the {code} cardiac device trial", params=[
        ("left ventricular ejection fraction", "percent", "min", 30, 48, 0),
        ("six-minute walk distance", "meters", "min", 150, 420, 0),
        ("NT-proBNP level", "picograms per milliliter", "max", 600, 2400, 0),
        ("estimated glomerular filtration rate", "milliliters per minute", "min", 30, 75, 0),
        ("resting heart rate", "beats per minute", "max", 60, 105, 0),
        ("serum potassium", "millimoles per liter", "max", 3.8, 5.2, 1),
        ("QRS duration", "milliseconds", "min", 120, 175, 0),
        ("systolic blood pressure", "millimeters of mercury", "min", 90, 135, 0),
        ("hemoglobin", "grams per deciliter", "min", 10, 15, 1),
        ("serum sodium", "millimoles per liter", "min", 133, 143, 0),
        ("body mass index", "kilograms per square meter", "max", 22, 39, 1),
        ("total cholesterol", "milligrams per deciliter", "max", 150, 260, 0),
        ("fasting glucose", "milligrams per deciliter", "max", 80, 145, 0),
        ("oxygen saturation", "percent", "min", 90, 98, 0)]),
    dict(domain="metabolic", event="enrollment of participant {code} in the {code} metabolic study", params=[
        ("glycated hemoglobin", "percent", "max", 6.5, 10.5, 1),
        ("fasting plasma glucose", "milligrams per deciliter", "max", 110, 210, 0),
        ("estimated glomerular filtration rate", "milliliters per minute", "min", 45, 95, 0),
        ("body mass index", "kilograms per square meter", "min", 25, 41, 1),
        ("triglycerides", "milligrams per deciliter", "max", 120, 380, 0),
        ("alanine aminotransferase", "units per liter", "max", 22, 78, 0),
        ("systolic blood pressure", "millimeters of mercury", "max", 120, 162, 0),
        ("HDL cholesterol", "milligrams per deciliter", "min", 32, 62, 0),
        ("C-peptide", "nanograms per milliliter", "min", 0.6, 3.2, 1),
        ("serum creatinine", "milligrams per deciliter", "max", 0.7, 1.6, 1),
        ("waist circumference", "centimeters", "min", 80, 118, 0),
        ("thyroid stimulating hormone", "milliunits per liter", "max", 0.5, 4.6, 1),
        ("resting heart rate", "beats per minute", "max", 58, 98, 0),
        ("vitamin D level", "nanograms per milliliter", "min", 18, 46, 0)]),
    dict(domain="neurology", event="enrollment of participant {code} in the {code} neurology protocol", params=[
        ("Mini-Mental State score", "points", "min", 20, 29, 0),
        ("creatinine clearance", "milliliters per minute", "min", 50, 105, 0),
        ("alanine aminotransferase", "units per liter", "max", 18, 66, 0),
        ("platelet count", "thousand per microliter", "min", 120, 310, 0),
        ("diastolic blood pressure", "millimeters of mercury", "max", 70, 102, 0),
        ("hemoglobin", "grams per deciliter", "min", 10.5, 15.5, 1),
        ("serum sodium", "millimoles per liter", "min", 134, 144, 0),
        ("body mass index", "kilograms per square meter", "min", 19, 33, 1),
        ("corrected QT interval", "milliseconds", "max", 410, 468, 0),
        ("fasting glucose", "milligrams per deciliter", "max", 82, 138, 0),
        ("total bilirubin", "milligrams per deciliter", "max", 0.5, 1.6, 1),
        ("resting heart rate", "beats per minute", "min", 52, 88, 0),
        ("serum calcium", "milligrams per deciliter", "max", 8.6, 10.4, 1),
        ("white blood cell count", "thousand per microliter", "min", 3.2, 9.0, 1)]),
    dict(domain="respiratory", event="enrollment of participant {code} in the {code} respiratory trial", params=[
        ("FEV1 percent predicted", "percent", "min", 40, 78, 0),
        ("oxygen saturation on room air", "percent", "min", 88, 97, 0),
        ("six-minute walk distance", "meters", "min", 180, 440, 0),
        ("eosinophil count", "cells per microliter", "max", 150, 620, 0),
        ("body mass index", "kilograms per square meter", "min", 18, 34, 1),
        ("resting respiratory rate", "breaths per minute", "max", 12, 24, 0),
        ("hemoglobin", "grams per deciliter", "min", 11, 16, 1),
        ("creatinine clearance", "milliliters per minute", "min", 48, 100, 0),
        ("systolic blood pressure", "millimeters of mercury", "max", 116, 156, 0),
        ("fasting glucose", "milligrams per deciliter", "max", 84, 140, 0),
        ("alanine aminotransferase", "units per liter", "max", 19, 64, 0),
        ("resting heart rate", "beats per minute", "max", 60, 100, 0),
        ("serum potassium", "millimoles per liter", "min", 3.6, 5.0, 1),
        ("carbon monoxide diffusing capacity", "percent predicted", "min", 40, 82, 0)]),
    dict(domain="nephrology", event="enrollment of participant {code} in the {code} renal study", params=[
        ("estimated glomerular filtration rate", "milliliters per minute", "min", 25, 68, 0),
        ("urine albumin-to-creatinine ratio", "milligrams per gram", "max", 30, 640, 0),
        ("serum potassium", "millimoles per liter", "max", 3.9, 5.4, 1),
        ("hemoglobin", "grams per deciliter", "min", 9.5, 14, 1),
        ("systolic blood pressure", "millimeters of mercury", "max", 120, 168, 0),
        ("serum phosphate", "milligrams per deciliter", "max", 2.7, 5.2, 1),
        ("serum bicarbonate", "millimoles per liter", "min", 18, 27, 0),
        ("intact parathyroid hormone", "picograms per milliliter", "max", 40, 320, 0),
        ("body mass index", "kilograms per square meter", "min", 19, 35, 1),
        ("fasting glucose", "milligrams per deciliter", "max", 86, 150, 0),
        ("serum calcium", "milligrams per deciliter", "min", 8.4, 10.0, 1),
        ("alanine aminotransferase", "units per liter", "max", 20, 60, 0),
        ("resting heart rate", "beats per minute", "max", 58, 96, 0),
        ("serum albumin", "grams per deciliter", "min", 3.2, 4.5, 1)]),
]

CODES = ["Larkspur", "Meridian", "Cypress", "Halcyon", "Verbena", "Solstice", "Marlowe",
         "Tamarind", "Cascade", "Wintergreen", "Bellflower", "Thistledown", "Sorrel", "Juniper",
         "Foxglove", "Mistral", "Peregrine", "Almandine", "Rosewood", "Calliope", "Hawthorn",
         "Delphine", "Currant", "Bramble", "Nightingale", "Sagebrush", "Yarrow", "Clementine",
         "Driftwood", "Embercress", "Fennel", "Gossamer", "Harrow", "Ivywood", "Juniperus",
         "Kestrel", "Lorimer", "Mulberry", "Nettle", "Oakhurst", "Plumbago", "Quillon",
         "Rowan", "Saffronel", "Tanager", "Umbral", "Verdigris", "Willowmere", "Xanthe",
         "Yewbank", "Zinnia", "Amaranth", "Boxwood", "Cedarly", "Dogwood", "Eldermere",
         "Ferncliff", "Gale", "Heathrow", "Iris"]

FIRST = ["A.R.", "M.T.", "S.K.", "J.P.", "L.N.", "R.V.", "C.B.", "D.M.", "K.O.", "N.F.",
         "P.G.", "T.H.", "E.S.", "B.W.", "O.D.", "H.L.", "V.C.", "G.A.", "Y.R.", "F.J."]
CLINICIANS = ["Dr. Okafor", "Dr. Bergstrom", "Dr. Castellano", "Dr. Devi", "Dr. Ellison",
              "Dr. Farhadi", "Dr. Gritsenko", "Dr. Halloran", "Dr. Imai", "Dr. Jovanovic",
              "Dr. Kessler", "Dr. Lindgren", "Dr. Moreau", "Dr. Nkemelu", "Dr. Ostrowski",
              "Dr. Pashkov", "Dr. Quraishi", "Dr. Renard", "Dr. Sato", "Dr. Thibault"]
VISITS = ["the baseline screening visit", "the week-two follow-up", "the intake assessment",
          "the pre-randomization workup", "the second screening encounter",
          "the confirmatory visit", "the enrollment clinic day", "the run-in evaluation"]
NARR = ["morning", "afternoon", "same-day", "scheduled", "rescheduled", "walk-in", "early", "late"]

# number-free distractor sentences (clinical register, no labs, no verdict language)
DISTRACTOR_T = [
    lambda r: f"At {r.choice(VISITS)}, {r.choice(CLINICIANS)} reviewed the participant's prior "
              f"medication history and confirmed that the consent form had been signed and witnessed.",
    lambda r: f"The coordinator noted that participant {mk_initials(r)} arrived for a {r.choice(NARR)} "
              f"appointment and that transportation to the site had been arranged by the family.",
    lambda r: f"A brief social history recorded by {r.choice(CLINICIANS)} described the participant as "
              f"a retired teacher living independently, with no reported difficulty completing daily tasks.",
    lambda r: f"Nursing staff documented that the phlebotomy draw was uneventful and that the sample "
              f"tubes were labeled and dispatched to the central laboratory without incident.",
    lambda r: f"During {r.choice(VISITS)}, the participant asked several questions about the study "
              f"schedule, which {r.choice(CLINICIANS)} answered before proceeding with the examination.",
    lambda r: f"The chart includes a note from {r.choice(CLINICIANS)} confirming that no changes to "
              f"concomitant therapy had been made since the previous contact with the study team.",
    lambda r: f"An addendum signed by the site pharmacist observed that drug accountability records "
              f"were reconciled and that no discrepancies required follow-up with the sponsor.",
    lambda r: f"The participant's spouse accompanied them to {r.choice(VISITS)} and provided a "
              f"collateral account of recent appetite and sleep, which was filed with the intake packet.",
    lambda r: f"A telephone contact logged by the {r.choice(NARR)} coordinator confirmed the next visit "
              f"window and reminded the participant to fast beforehand, per the written instructions.",
    lambda r: f"{r.choice(CLINICIANS)} recorded that the physical examination was grossly unremarkable "
              f"and that the participant tolerated the assessment battery without needing a break.",
    lambda r: f"The regulatory binder was updated to reflect that the current protocol version and "
              f"the local ethics approval letter were both on file at the time of this encounter.",
    lambda r: f"A short note from the study nurse mentioned that educational materials were provided "
              f"and that the participant demonstrated understanding of the visit calendar.",
]

# lab-reading sentence templates (identical structure for policy and non-policy labs)
PARAM_T = [
    "The {p} was reported as {v} {u} on the laboratory panel.",
    "Bloodwork drawn at screening returned a {p} of {v} {u}.",
    "The {p} measured {v} {u} at this visit, per the central lab report.",
    "Per the results annex, the {p} came back at {v} {u}.",
    "The recorded {p} for this participant was {v} {u}.",
    "Laboratory findings listed the {p} at {v} {u}.",
]


def mk_initials(r):
    return r.choice(FIRST)


def fmt_val(v, dec):
    return int(round(v)) if dec == 0 else round(v, dec)


def gen_items(seed=90210, n=60):
    rng = random.Random(seed)
    # 30 APPROVED (eligible), 30 DENIED (excluded, exactly one failing criterion), balanced fail slot
    patterns = [(True, None)] * 30 + [(False, k % 3) for k in range(30)]
    rng.shuffle(patterns)
    codes = rng.sample(CODES, n)
    items = []
    for i, (approved, fail_slot) in enumerate(patterns):
        used_sentences = set()  # uniqueness within an item; distractors may recur across items
        proto = PROTOCOLS[i % len(PROTOCOLS)]
        drng = random.Random(60000 + i)
        chosen = drng.sample(proto["params"], 12)
        pol_idx = sorted(drng.sample(range(12), 3))
        # metric-confound guard: every policy value must be uniquely retained() among all 12
        # values, so `pol_vals` is the set that both draws must stay clear of. Non-policy
        # collisions with each other are harmless (they are never the scored witness).
        forbidden, pol_vals, plist = set(), [], []
        for k, pi in enumerate(pol_idx):
            name, unit, direction, lo, hi, dec = chosen[pi]
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)),
                        1 if dec else 0)
            forbidden.add(float(thr))
            span = max(abs(thr) * 0.3, 1.0 if dec == 0 else 0.5)
            passes = (fail_slot is None) or (k != fail_slot)
            for _ in range(400):
                v = fmt_val(draw_value(drng, thr, direction, passes, span, forbidden), dec)
                ok = (v <= thr) if direction == "max" else (v >= thr)
                if ok == passes and not collides(v, pol_vals):
                    break
            else:
                raise RuntimeError("policy value draw failed")
            forbidden.add(float(v))
            pol_vals.append(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=True, dir=direction,
                              thr=thr, value=v, passes=passes, dec=dec))
        for pi in range(12):
            if pi in pol_idx:
                continue
            name, unit, direction, lo, hi, dec = chosen[pi]
            for _ in range(400):
                v = fmt_val(drng.uniform(lo, hi), dec)
                if dec and abs(v - round(v)) < 0.005:
                    continue
                if float(v) in forbidden or collides(v, pol_vals):
                    continue
                break
            else:
                raise RuntimeError("nonpolicy value draw failed")
            forbidden.add(float(v))
            plist.append(dict(idx=pi, name=name, unit=unit, policy=False, value=v, dec=dec))
        plist.sort(key=lambda d: d["idx"])
        pol = [d for d in plist if d["policy"]]
        truth = "APPROVED" if all(d["passes"] for d in pol) else "DENIED"
        assert (truth == "APPROVED") == approved
        failing = None if approved else pol[fail_slot]["name"]
        code = codes[i]
        event = proto["event"].format(code=code)
        intro = (f"PARTICIPANT SCREENING CHART — Record {code}. This chart collects laboratory "
                 f"results, vital signs, and clinic notes gathered for {event}. Entries are listed "
                 f"in the order they were filed by the study team and have not been reviewed for any "
                 f"specific purpose.")
        param_sents = []
        for d in plist:
            for _ in range(80):
                s = drng.choice(PARAM_T).format(p=d["name"], v=d["value"], u=d["unit"])
                if s not in used_sentences:
                    used_sentences.add(s)
                    param_sents.append(s)
                    break
            else:
                raise RuntimeError("param sentence uniqueness failed")
        distractors = []
        for _ in range(11):
            for _ in range(120):
                s = drng.choice(DISTRACTOR_T)(drng)
                if s not in used_sentences:
                    used_sentences.add(s)
                    distractors.append(s)
                    break
            else:
                raise RuntimeError("distractor uniqueness failed")
        body = param_sents + distractors
        drng.shuffle(body)
        paras, k = [], 0
        while k < len(body):
            step = drng.choice([3, 4, 5])
            paras.append(" ".join(body[k:k + step]))
            k += step
        doc = intro + "\n\n" + "\n\n".join(paras) + "\n\nEnd of chart."
        policy_text = (f"ELIGIBILITY POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
                       f"{cond_clause(pol[0]['name'], pol[0]['unit'], pol[0]['dir'], pol[0]['thr'])} AND "
                       f"{cond_clause(pol[1]['name'], pol[1]['unit'], pol[1]['dir'], pol[1]['thr'])} AND "
                       f"{cond_clause(pol[2]['name'], pol[2]['unit'], pol[2]['dir'], pol[2]['thr'])}; "
                       f"otherwise it is DENIED.")
        items.append(dict(
            id=f"clin{i:02d}", domain=proto["domain"], code=code, event=event, truth=truth,
            failing_param=failing, fail_slot=fail_slot, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            word_count=len(doc.split()), document=doc))
    return items


def selfcheck(items):
    """Guard the three confounds mechanically before any spend."""
    import re
    problems = []
    # "enrollment ... in the ... trial" is the cover-story event name (like the incident
    # corpus's "release of the X batch"), not a statement of THIS patient's status. Genuine
    # leaks are per-patient verdict/spec words or a stated threshold — check the body only.
    VERDICT_WORDS = re.compile(r"eligib|exclud|ineligib|criteri|threshold|out of range|"
                               r"out-of-range|out of spec|abnormal|too (high|low)|exceed|below "
                               r"the limit|does not (meet|qualify)|qualif", re.I)
    for it in items:
        body = it["document"].split("\n\n", 1)[1]  # drop the intro paragraph
        # metric: every policy value must be uniquely retained() among the 12 values
        vals = [p["value"] for p in it["parameters"]]
        for p in it["parameters"]:
            if not p["policy"]:
                continue
            hits = sum(retained(f"{v}", p["value"]) for v in vals)
            if hits != 1:
                problems.append((it["id"], "value-collision", p["name"], hits))
        # verdict leak: no eligibility/threshold language in the chart body
        m = VERDICT_WORDS.search(body)
        if m:
            problems.append((it["id"], "verdict-leak", m.group(0)))
        # failing param must map back to itself via match_param
        if it["failing_param"]:
            mp = match_param(it["failing_param"], it["parameters"])
            if mp != it["failing_param"]:
                problems.append((it["id"], "param-unmatch", it["failing_param"], mp))
    return problems


if __name__ == "__main__":
    items = gen_items()
    problems = selfcheck(items)
    with open(ITEMS, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    den = [it for it in items if it["truth"] == "DENIED"]
    wc = [it["word_count"] for it in items]
    print(f"generated {len(items)} items ({len(den)} DENIED); words min={min(wc)} "
          f"max={max(wc)} mean={sum(wc)/len(wc):.0f}")
    print(f"fail slots: {[sum(it['fail_slot'] == k for it in items) for k in (0,1,2)]}")
    print(f"domains: {sorted(set(it['domain'] for it in items))}")
    print(f"selfcheck problems: {len(problems)}")
    for p in problems[:20]:
        print("  ", p)
