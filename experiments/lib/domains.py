#!/usr/bin/env python3
"""Shared confound-guarded corpus generator for the 2026-07-06 high-power + domain campaigns.

One item schema (identical to the v5 incident corpus, so runner3/runner5 scoring —
retained / parse_which / match_param / ANS_RE — applies unchanged across every domain):

    id, domain, code, event, truth (APPROVED|DENIED), failing_param, fail_slot,
    policy_text, parameters[{name,unit,value,policy,[dir,thr,passes]}], word_count, document

The *verdict interface* is held constant (APPROVED/DENIED tokens, conjunction-of-3-thresholds
policy, DENIED = exactly one failing criterion) so the machinery transfers and the campaigns
isolate DOMAIN / SURFACE generalization. Only the surface varies: parameter names+units, the
document register (file header, reading sentences, number-free distractors), and the event.

Confound guards (the full v2–v5 + 2026-07-06 checklist):
  - salience:      policy and non-policy readings share the same sentence templates, shuffled.
  - verdict leak:  the document never states the verdict, thresholds, or spec/pass/fail language.
  - metric:        all sampled values pairwise distinct and non-round; every policy value is
                   UNIQUELY retained() among the item's values (collides() guard) so the string
                   check cannot false-match a non-policy reading.
  - candidate/parse: unrelated to generation, handled at scoring time (last-anchor parser,
                   candidate-set disclosure documented per prereg).

Stdlib only, seeded, no LLM. Import gen_items(domain_key, seed, n) and selfcheck(items).
"""
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GROK = os.path.join(HERE, "..", "grok-pilots", "2026-07-03")
sys.path.insert(0, os.path.join(GROK, "v2"))
sys.path.insert(0, os.path.join(GROK, "v3"))
from runner2 import cond_clause, draw_value          # exact threshold/value logic
from runner3 import retained, match_param            # metric functions (also used in guards)


# ── domain specs ──────────────────────────────────────────────────────────────
# Each: params = [(name, unit, dir, lo, hi, dec)], with 14 candidates (12 sampled per item).
# header(code,event) -> intro paragraph; event = "<gerund> of <code>"; param_t / distractor_t
# are lists of format templates ({p},{v},{u} for readings; a lambda(rng) for distractors).

def _val(v, dec):
    return int(round(v)) if dec == 0 else round(v, dec)


DOMAINS = {
    # 1 ── operations go/no-go (the original incident register) ───────────────
    "ops_incident": dict(
        label="operations go/no-go",
        event="the go/no-go review of operation {code}",
        header=lambda code, event: (
            f"INCIDENT REVIEW FILE — Operation {code}. This file collects readings and "
            f"observations logged during {event}. Entries appear in the order received by the "
            f"Operation {code} duty desk and have not been prioritized or adjudicated."),
        end="End of file.",
        params=[
            ("propellant tank ullage pressure", "bar", "min", 3.0, 7.4, 2),
            ("battery bus impedance", "milliohms", "max", 18, 42, 2),
            ("gyro drift rate", "degrees per hour", "max", 0.2, 0.9, 2),
            ("thermal blanket coverage", "percent", "min", 70, 99, 1),
            ("umbilical release delay", "seconds", "max", 2.0, 5.5, 2),
            ("guidance solution confidence", "percent", "min", 88, 99, 1),
            ("coolant loop flow rate", "liters per minute", "min", 40, 96, 1),
            ("telemetry downlink margin", "decibels", "min", 3.0, 9.0, 1),
            ("avionics bus load", "percent", "max", 30, 78, 1),
            ("seal torque retention", "newton meters", "min", 60, 92, 2),
            ("condenser outlet temperature", "degrees celsius", "max", 20, 55, 2),
            ("particulate count", "counts per liter", "max", 40, 120, 1),
            ("star tracker residual", "arcseconds", "max", 8, 30, 1),
            ("reserve charge margin", "percent", "min", 60, 95, 2)],
        param_t=[
            "The {p} was logged at {v} {u} by the duty controller.",
            "A reading of {v} {u} for the {p} appears in the console log.",
            "The {p} registered {v} {u} during the review window.",
            "Instrumentation reported the {p} at {v} {u}.",
            "The {p} for this operation stood at {v} {u}.",
            "Recorded telemetry lists the {p} as {v} {u}."],
        distractor_t=[
            lambda r: "The duty desk noted that the shift handover was completed on schedule and "
                      "that all console positions were staffed for the review window.",
            lambda r: "A maintenance memo confirmed that routine servicing had been signed off and "
                      "that no open work orders remained against the affected subsystem.",
            lambda r: "The controller recorded that voice loops were nominal and that the recovery "
                      "team acknowledged the standard pre-review checklist.",
            lambda r: "An annotation from the range office observed that weather at the site was "
                      "within the general advisory and that visibility was unrestricted.",
            lambda r: "The log includes a note that badge access to the control room was reconciled "
                      "and that the visitor manifest matched the escort roster.",
            lambda r: "Ground crew reported that cabling was dressed and secured and that connector "
                      "keying was verified against the reference photographs.",
            lambda r: "A brief entry mentioned that the backup generator had completed its scheduled "
                      "exercise cycle and returned to standby without comment.",
            lambda r: "The operations summary observed that the review proceeded in the usual order "
                      "and that no external interruptions were recorded by the desk."]),

    # 2 ── clinical trial enrollment (condensed from gen_clinical) ────────────
    "clinical_enroll": dict(
        label="clinical trial enrollment",
        event="enrollment of participant {code} in the {code} study cohort",
        header=lambda code, event: (
            f"PARTICIPANT SCREENING CHART — Record {code}. This chart collects laboratory results, "
            f"vital signs, and clinic notes gathered for {event}. Entries are listed in the order "
            f"they were filed by the study team and have not been reviewed for any specific purpose."),
        end="End of chart.",
        params=[
            ("absolute neutrophil count", "cells per microliter", "min", 1500, 4200, 0),
            ("platelet count", "thousand per microliter", "min", 100, 320, 0),
            ("creatinine clearance", "milliliters per minute", "min", 45, 110, 0),
            ("total bilirubin", "milligrams per deciliter", "max", 0.6, 1.8, 2),
            ("left ventricular ejection fraction", "percent", "min", 50, 68, 1),
            ("corrected QT interval", "milliseconds", "max", 400, 470, 1),
            ("hemoglobin", "grams per deciliter", "min", 9.0, 14.5, 2),
            ("alanine aminotransferase", "units per liter", "max", 20, 70, 1),
            ("serum albumin", "grams per deciliter", "min", 3.0, 4.6, 2),
            ("fasting glucose", "milligrams per deciliter", "max", 85, 135, 1),
            ("body mass index", "kilograms per square meter", "min", 18.5, 31, 2),
            ("systolic blood pressure", "millimeters of mercury", "max", 118, 158, 1),
            ("estimated glomerular filtration rate", "milliliters per minute", "min", 45, 95, 1),
            ("triglycerides", "milligrams per deciliter", "max", 120, 380, 1)],
        param_t=[
            "The {p} was reported as {v} {u} on the laboratory panel.",
            "Bloodwork drawn at screening returned a {p} of {v} {u}.",
            "The {p} measured {v} {u} at this visit, per the central lab report.",
            "Per the results annex, the {p} came back at {v} {u}.",
            "The recorded {p} for this participant was {v} {u}.",
            "Laboratory findings listed the {p} at {v} {u}."],
        distractor_t=[
            lambda r: "The coordinator reviewed the participant's prior medication history and "
                      "confirmed that the consent form had been signed and witnessed.",
            lambda r: "A brief social history described the participant as living independently, "
                      "with no reported difficulty completing daily tasks.",
            lambda r: "Nursing staff documented that the phlebotomy draw was uneventful and that "
                      "the sample tubes were labeled and dispatched to the central laboratory.",
            lambda r: "The chart includes a note confirming that no changes to concomitant therapy "
                      "had been made since the previous contact with the study team.",
            lambda r: "An addendum from the site pharmacist observed that drug accountability "
                      "records were reconciled and that no discrepancies required follow-up.",
            lambda r: "The participant's spouse provided a collateral account of recent appetite "
                      "and sleep, which was filed with the intake packet.",
            lambda r: "A telephone contact confirmed the next visit window and reminded the "
                      "participant to fast beforehand, per the written instructions.",
            lambda r: "The study nurse recorded that educational materials were provided and that "
                      "the participant demonstrated understanding of the visit calendar."]),

    # 3 ── software CI / release gate ─────────────────────────────────────────
    "ci_release": dict(
        label="software release gate",
        event="the release-gate review of build {code}",
        header=lambda code, event: (
            f"RELEASE READINESS RECORD — Build {code}. This record collects the automated checks "
            f"and reviewer notes gathered for {event}. Entries appear in the order the CI system "
            f"emitted them and have not been triaged against any release policy."),
        end="End of record.",
        params=[
            ("unit test pass rate", "percent", "min", 92, 100, 2),
            ("p95 request latency", "milliseconds", "max", 120, 480, 1),
            ("line coverage", "percent", "min", 68, 94, 1),
            ("error budget remaining", "percent", "min", 15, 90, 1),
            ("cold start time", "milliseconds", "max", 300, 1400, 1),
            ("bundle size", "kilobytes", "max", 480, 1600, 1),
            ("peak heap usage", "megabytes", "max", 220, 900, 1),
            ("flaky test count", "tests", "max", 0, 9, 0),
            ("open severity-one defects", "defects", "max", 0, 4, 0),
            ("dependency audit findings", "findings", "max", 0, 12, 0),
            ("build reproducibility", "percent", "min", 90, 100, 2),
            ("rollback drill success", "percent", "min", 80, 100, 1),
            ("mean time to acknowledge", "minutes", "max", 3, 25, 1),
            ("canary error rate", "per million requests", "max", 20, 300, 1)],
        param_t=[
            "The {p} came back at {v} {u} in the pipeline summary.",
            "CI reported the {p} as {v} {u} for this build.",
            "The {p} was measured at {v} {u} on the release branch.",
            "Pipeline output listed the {p} at {v} {u}.",
            "The recorded {p} for build was {v} {u}.",
            "The dashboard showed the {p} at {v} {u}."],
        distractor_t=[
            lambda r: "The release manager noted that the change log had been assembled and that "
                      "every merged pull request carried a linked ticket.",
            lambda r: "A comment confirmed that the on-call rotation was staffed for the deployment "
                      "window and that the runbook link resolved correctly.",
            lambda r: "The record includes a note that feature flags for the release were reviewed "
                      "and that the default states matched the rollout plan.",
            lambda r: "An entry observed that documentation for the new endpoints had been drafted "
                      "and queued for publication alongside the release.",
            lambda r: "Reviewers acknowledged that the staging soak had run overnight and that the "
                      "synthetic traffic generator reported no operator alerts.",
            lambda r: "The pipeline logged that container images were signed and pushed to the "
                      "registry and that the manifest digests were recorded.",
            lambda r: "A short note mentioned that the database migration had been rehearsed on a "
                      "shadow copy and reviewed by the owning team.",
            lambda r: "The summary observed that localization strings were regenerated and that no "
                      "untranslated keys remained in the primary locales."]),

    # 4 ── consumer loan underwriting ─────────────────────────────────────────
    "loan_underwrite": dict(
        label="loan underwriting",
        event="underwriting of application {code}",
        header=lambda code, event: (
            f"UNDERWRITING WORKSHEET — Application {code}. This worksheet collects the figures and "
            f"file notes gathered for {event}. Entries appear in the order the processing system "
            f"attached them and have not been evaluated against any lending guideline."),
        end="End of worksheet.",
        params=[
            ("credit score", "points", "min", 580, 810, 0),
            ("debt-to-income ratio", "percent", "max", 22, 52, 1),
            ("loan-to-value ratio", "percent", "max", 60, 97, 1),
            ("cash reserves", "months of payments", "min", 1, 11, 1),
            ("employment tenure", "years", "min", 0.5, 9, 1),
            ("payment-to-income ratio", "percent", "max", 12, 40, 1),
            ("recent credit inquiries", "inquiries", "max", 0, 8, 0),
            ("documented annual income", "thousand dollars", "min", 38, 180, 1),
            ("delinquencies past two years", "accounts", "max", 0, 5, 0),
            ("down payment", "percent", "min", 3, 30, 1),
            ("revolving utilization", "percent", "max", 8, 68, 1),
            ("appraised value gap", "percent", "max", 0, 9, 1),
            ("months at current address", "months", "min", 6, 96, 0),
            ("liquid post-close assets", "thousand dollars", "min", 4, 90, 1)],
        param_t=[
            "The {p} was entered as {v} {u} on the application.",
            "The processor recorded a {p} of {v} {u}.",
            "The file lists the {p} at {v} {u}.",
            "Per the credit summary, the {p} was {v} {u}.",
            "The stated {p} for this applicant was {v} {u}.",
            "The worksheet shows the {p} at {v} {u}."],
        distractor_t=[
            lambda r: "The processor noted that the applicant's identity documents were verified and "
                      "that the file contained a signed authorization to pull credit.",
            lambda r: "A file comment confirmed that the property address matched the appraisal "
                      "order and that the title search had been requested.",
            lambda r: "The worksheet includes a note that the applicant preferred email contact and "
                      "that a preliminary disclosure packet had been mailed.",
            lambda r: "An entry observed that the co-applicant section was left blank and that the "
                      "application was submitted as a single borrower.",
            lambda r: "The loan officer recorded that the rate lock preferences were discussed and "
                      "that a follow-up call was scheduled for the closing timeline.",
            lambda r: "A note mentioned that gift funds, if any, would require a letter and that "
                      "none had been indicated on the intake form.",
            lambda r: "The file logged that the applicant's bank provided statements covering the "
                      "requested period and that the pages were legible.",
            lambda r: "A short comment observed that the homeowners insurance quote was outstanding "
                      "and would be added before the file advanced."]),

    # 5 ── vendor SLA / contract compliance ───────────────────────────────────
    "vendor_sla": dict(
        label="vendor SLA compliance",
        event="the quarterly compliance review of vendor {code}",
        header=lambda code, event: (
            f"VENDOR PERFORMANCE FILE — Contract {code}. This file collects the metrics and account "
            f"notes gathered for {event}. Entries appear in the order the vendor portal exported "
            f"them and have not been assessed against the master services agreement."),
        end="End of file.",
        params=[
            ("service uptime", "percent", "min", 97.0, 99.99, 2),
            ("average resolution time", "hours", "max", 2, 40, 1),
            ("on-time delivery rate", "percent", "min", 82, 99, 1),
            ("defect escape rate", "per thousand units", "max", 1, 22, 1),
            ("first-response time", "minutes", "max", 8, 90, 1),
            ("invoice accuracy", "percent", "min", 94, 100, 2),
            ("security questionnaire score", "points", "min", 70, 98, 1),
            ("change failure rate", "percent", "max", 2, 24, 1),
            ("staffing coverage", "percent", "min", 85, 100, 1),
            ("data residency compliance", "percent", "min", 90, 100, 2),
            ("escalation acknowledgment", "minutes", "max", 5, 55, 1),
            ("backup restore success", "percent", "min", 88, 100, 1),
            ("contractual penalty exposure", "thousand dollars", "max", 0, 45, 1),
            ("audit finding closure", "percent", "min", 75, 100, 1)],
        param_t=[
            "The {p} was reported as {v} {u} in the quarterly export.",
            "The portal recorded a {p} of {v} {u}.",
            "The file lists the {p} at {v} {u}.",
            "Per the account summary, the {p} was {v} {u}.",
            "The measured {p} for this vendor was {v} {u}.",
            "The scorecard shows the {p} at {v} {u}."],
        distractor_t=[
            lambda r: "The account manager noted that the quarterly business review had been "
                      "scheduled and that the agenda was circulated to both parties.",
            lambda r: "A file comment confirmed that the primary contacts were current and that the "
                      "escalation tree had been re-verified during onboarding refresh.",
            lambda r: "The record includes a note that the vendor's certificates of insurance were "
                      "on file and that the coverage dates were current.",
            lambda r: "An entry observed that the statement of work amendment was in legal review "
                      "and that no pricing changes were pending.",
            lambda r: "The portal logged that the monthly status deck had been delivered and that "
                      "the format matched the reporting template.",
            lambda r: "A note mentioned that the vendor requested a maintenance window and that the "
                      "proposed timing avoided the reporting freeze.",
            lambda r: "The account team recorded that a satisfaction survey had been sent to the "
                      "stakeholders and that responses were still being collected.",
            lambda r: "A short comment observed that the relationship had no open disputes logged "
                      "and that prior action items were marked resolved."]),

    # 6 ── security vulnerability triage ──────────────────────────────────────
    "sec_triage": dict(
        label="security exposure triage",
        event="the exposure triage of asset {code}",
        header=lambda code, event: (
            f"EXPOSURE TRIAGE SHEET — Asset {code}. This sheet collects the scanner outputs and "
            f"analyst notes gathered for {event}. Entries appear in the order the tooling produced "
            f"them and have not been ranked against the acceptance policy."),
        end="End of sheet.",
        params=[
            ("CVSS base score", "points", "max", 3.0, 9.6, 1),
            ("days since patch available", "days", "max", 2, 120, 0),
            ("exposed attack surface", "percent", "max", 4, 70, 1),
            ("authentication strength", "points", "min", 40, 96, 1),
            ("blast radius", "percent of fleet", "max", 1, 45, 1),
            ("mean time to detect", "hours", "max", 1, 30, 1),
            ("log coverage", "percent", "min", 60, 98, 1),
            ("privileged accounts affected", "accounts", "max", 0, 14, 0),
            ("network segmentation score", "points", "min", 45, 95, 1),
            ("exploit maturity index", "points", "max", 5, 88, 1),
            ("data sensitivity rating", "points", "max", 10, 92, 1),
            ("backup recency", "hours", "max", 2, 70, 1),
            ("endpoint agent coverage", "percent", "min", 72, 100, 1),
            ("mean time to remediate", "days", "max", 1, 28, 1)],
        param_t=[
            "The {p} came back at {v} {u} in the scan results.",
            "The scanner recorded a {p} of {v} {u}.",
            "The sheet lists the {p} at {v} {u}.",
            "Per the analyst summary, the {p} was {v} {u}.",
            "The observed {p} for this asset was {v} {u}.",
            "Tooling reported the {p} at {v} {u}."],
        distractor_t=[
            lambda r: "The analyst noted that the asset inventory record was current and that the "
                      "business owner had been identified for notification.",
            lambda r: "A sheet comment confirmed that the scanning credentials were valid and that "
                      "the authenticated scan completed without connection errors.",
            lambda r: "The record includes a note that the change advisory board had a standing "
                      "slot available should remediation require a maintenance window.",
            lambda r: "An entry observed that the asset was tagged to the correct environment and "
                      "that the ownership metadata matched the configuration database.",
            lambda r: "The tooling logged that a prior finding on an unrelated component had been "
                      "closed and archived with reviewer sign-off.",
            lambda r: "A note mentioned that threat intelligence feeds were current and that no "
                      "targeted campaign against the sector had been reported this cycle.",
            lambda r: "The analyst recorded that the runbook for this asset class was linked and "
                      "that the escalation contact list had been reviewed.",
            lambda r: "A short comment observed that the asset's monitoring dashboard was reachable "
                      "and that alert routing had been confirmed during the last drill."]),
}

DOMAIN_KEYS = list(DOMAINS.keys())

CODES = ["Larkspur", "Meridian", "Cypress", "Halcyon", "Verbena", "Solstice", "Marlowe",
         "Tamarind", "Cascade", "Wintergreen", "Bellflower", "Thistledown", "Sorrel", "Juniper",
         "Foxglove", "Mistral", "Peregrine", "Almandine", "Rosewood", "Calliope", "Hawthorn",
         "Delphine", "Currant", "Bramble", "Nightingale", "Sagebrush", "Yarrow", "Clementine",
         "Driftwood", "Embercress", "Fennel", "Gossamer", "Harrow", "Ivywood", "Kestrel",
         "Lorimer", "Mulberry", "Nettle", "Oakhurst", "Plumbago", "Quillon", "Rowan", "Saffron",
         "Tanager", "Umbral", "Verdigris", "Willowmere", "Xanthe", "Yewbank", "Zinnia", "Amaranth",
         "Boxwood", "Cedarly", "Dogwood", "Eldermere", "Ferncliff", "Galewind", "Heathrow", "Iris",
         "Jessamine", "Kingfisher", "Lowarch", "Moorland", "Norwood", "Ondine", "Pemberton",
         "Quicksilver", "Redpoll", "Starling", "Thornfield", "Ashgrove", "Briarwood", "Coldharbor",
         "Deepwell", "Evermoor", "Fairlight", "Grayling", "Hollybrook", "Inglewood", "Jetstream"]


# Neutral connectors prepended to distractor sentences: multiply the distractor space
# (8 templates x ~11 leads = ~88 unique/domain) and give cross-item variety without
# introducing numbers or verdict language. The base sentence's first letter is lowercased.
LEADS = ["Separately, ", "For the record, ", "In addition, ", "As background, ",
         "For completeness, ", "By way of context, ", "Also of note, ", "For reference, ",
         "As a housekeeping item, ", "For the file, ", "On a procedural note, "]


def _distractor(spec, drng, base_counts, used, max_uses=2):
    # each base distractor may appear at most `max_uses` times per item, always with a
    # different connector — enough facts for a ~450-word document without any single fact
    # recurring more than twice. base_counts: {base_index: uses}.
    n_bases = len(spec["distractor_t"])
    for _ in range(400):
        bi = drng.randrange(n_bases)
        if base_counts.get(bi, 0) >= max_uses:
            continue
        base = spec["distractor_t"][bi](drng)
        s = drng.choice(LEADS) + base[0].lower() + base[1:]
        if s not in used:
            used.add(s)
            base_counts[bi] = base_counts.get(bi, 0) + 1
            return s
    raise RuntimeError("distractor uniqueness failed")


def collides(v, forbidden):
    return any(retained(f"{v}", f) or retained(f"{f}", v) for f in forbidden)


def gen_items(domain_key, seed, n):
    """Generate n items for one domain: n//2 APPROVED, n//2 DENIED (one failing criterion,
    fail-slot balanced). Deterministic in (domain_key, seed, n)."""
    spec = DOMAINS[domain_key]
    rng = random.Random(seed)
    half = n // 2
    patterns = [(True, None)] * half + [(False, k % 3) for k in range(n - half)]
    rng.shuffle(patterns)
    if n > len(CODES):
        codes = [f"{rng.choice(CODES)}-{i:03d}" for i in range(n)]
    else:
        codes = rng.sample(CODES, n)
    items = []
    for i, (approved, fail_slot) in enumerate(patterns):
        used = set()
        drng = random.Random((seed * 100003) ^ (i + 1))
        chosen = drng.sample(spec["params"], 12)
        pol_idx = sorted(drng.sample(range(12), 3))
        forbidden, pol_vals, plist = set(), [], []
        for k, pi in enumerate(pol_idx):
            name, unit, direction, lo, hi, dec = chosen[pi]
            thr = round(drng.uniform(lo + 0.25 * (hi - lo), hi - 0.25 * (hi - lo)),
                        1 if dec else 0)
            forbidden.add(float(thr))
            span = max(abs(thr) * 0.3, 1.0 if dec == 0 else 0.5)
            passes = (fail_slot is None) or (k != fail_slot)
            for _ in range(600):
                v = _val(draw_value(drng, thr, direction, passes, span, forbidden), dec)
                ok = (v <= thr) if direction == "max" else (v >= thr)
                if ok == passes and not collides(v, pol_vals):
                    break
            else:
                raise RuntimeError(f"{domain_key} item {i}: policy value draw failed")
            forbidden.add(float(v))
            pol_vals.append(v)
            plist.append(dict(idx=pi, name=name, unit=unit, policy=True, dir=direction,
                              thr=thr, value=v, passes=passes, dec=dec))
        for pi in range(12):
            if pi in pol_idx:
                continue
            name, unit, direction, lo, hi, dec = chosen[pi]
            for _ in range(600):
                v = _val(drng.uniform(lo, hi), dec)
                if dec and abs(v - round(v)) < 0.005:
                    continue
                if float(v) in forbidden or collides(v, pol_vals):
                    continue
                break
            else:
                raise RuntimeError(f"{domain_key} item {i}: nonpolicy value draw failed")
            forbidden.add(float(v))
            plist.append(dict(idx=pi, name=name, unit=unit, policy=False, value=v, dec=dec))
        plist.sort(key=lambda d: d["idx"])
        pol = [d for d in plist if d["policy"]]
        truth = "APPROVED" if all(d["passes"] for d in pol) else "DENIED"
        assert (truth == "APPROVED") == approved
        failing = None if approved else pol[fail_slot]["name"]
        code = codes[i]
        event = spec["event"].format(code=code)
        intro = spec["header"](code, event)
        param_sents = []
        for d in plist:
            for _ in range(120):
                s = drng.choice(spec["param_t"]).format(p=d["name"], v=d["value"], u=d["unit"])
                if s not in used:
                    used.add(s)
                    param_sents.append(s)
                    break
            else:
                raise RuntimeError(f"{domain_key} item {i}: param sentence uniqueness failed")
        # 11 distractors, each base used at most twice (varied connectors) — ~450-word docs
        # with no fact recurring more than twice.
        base_counts = {}
        distractors = [_distractor(spec, drng, base_counts, used) for _ in range(11)]
        body = param_sents + distractors
        drng.shuffle(body)
        paras, k = [], 0
        while k < len(body):
            step = drng.choice([3, 4, 5])
            paras.append(" ".join(body[k:k + step]))
            k += step
        doc = intro + "\n\n" + "\n\n".join(paras) + "\n\n" + spec["end"]
        policy_text = (f"POLICY: {event[0].upper() + event[1:]} is APPROVED only if "
                       f"{cond_clause(pol[0]['name'], pol[0]['unit'], pol[0]['dir'], pol[0]['thr'])} AND "
                       f"{cond_clause(pol[1]['name'], pol[1]['unit'], pol[1]['dir'], pol[1]['thr'])} AND "
                       f"{cond_clause(pol[2]['name'], pol[2]['unit'], pol[2]['dir'], pol[2]['thr'])}; "
                       f"otherwise it is DENIED.")
        items.append(dict(
            id=f"{domain_key}-{i:03d}", domain=domain_key, code=code, event=event, truth=truth,
            failing_param=failing, fail_slot=fail_slot, policy_text=policy_text,
            parameters=[dict(name=d["name"], unit=d["unit"], value=d["value"], policy=d["policy"],
                             **({"dir": d["dir"], "thr": d["thr"], "passes": d["passes"]}
                                if d["policy"] else {})) for d in plist],
            word_count=len(doc.split()), document=doc))
    return items


# Genuine verdict/threshold-adjudication language about THIS item's outcome. Word-boundary
# anchored, phrase-level where a bare token would be ambiguous. Parameter names (which
# legitimately contain "pass rate", "failure rate", "escalation" and are disclosed in
# policy_text anyway) are stripped from the body before this runs, so they never false-trip.
VERDICT_WORDS = re.compile(
    r"\b(approved|denied|rejected?|eligible|ineligible|excluded?|disqualif\w*|compliant|"
    r"non-?compliant|adjudicat\w*|flagged)\b|"
    r"\b(out of|out-of)\s+(spec|range|tolerance)\b|"
    r"\bwithin (spec|range|limits|tolerance)\b|"
    r"\b(exceeds?|below|meets?|satisfies|violat\w+|breach\w*)\s+(the\s+)?"
    r"(threshold|limit|criteri\w+|policy|requirement|minimum|maximum)\b|"
    r"\bdoes not (meet|qualify|satisfy)\b", re.I)


def selfcheck(items):
    """Mechanically guard the three generation confounds before any spend."""
    problems = []
    for it in items:
        body = it["document"].split("\n\n", 1)[1]  # drop the header paragraph (cover-story only)
        # strip the item's own parameter names — they are legitimate domain vocabulary and are
        # already disclosed in policy_text; a genuine leak is verdict/threshold language ABOUT
        # the reading, not the metric name itself.
        scan = body
        for p in it["parameters"]:
            scan = scan.replace(p["name"], " ")
        vals = [p["value"] for p in it["parameters"]]
        for p in it["parameters"]:
            if not p["policy"]:
                continue
            hits = sum(retained(f"{v}", p["value"]) for v in vals)
            if hits != 1:
                problems.append((it["id"], "value-collision", p["name"], hits))
        m = VERDICT_WORDS.search(scan)
        if m:
            problems.append((it["id"], "verdict-leak", m.group(0)))
        if it["failing_param"]:
            if match_param(it["failing_param"], it["parameters"]) != it["failing_param"]:
                problems.append((it["id"], "param-unmatch", it["failing_param"]))
    return problems
