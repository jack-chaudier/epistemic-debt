#!/usr/bin/env python3
"""Iterated compaction, length-clamped — settlement cost vs compound interest.
See prereg_clamped.md (FROZEN 2026-07-09 before any API call).

Discriminates two opposed frozen predictors for witness decay under iterated compaction:
  structural (contraction-gated hazard h = h0 + sigma*max(0, 1 - L_{r+1}/L_r), pooled
  (h0,sigma)=(0.002,0.48)) -> clamped per-round survival >= 0.98, net S8/S2 decay <= 0.07
  fitted-geometric (rho is a model constant) -> S8/S2 = rho^6 (grok 0.65, haiku 0.68, gpt 0.91)

Arms:
  A (clamp): grok/haiku/gpt, R=8, W=40; reject-and-retry (max 3 attempts) unless realized
    length in [36,44] words; keep first in-band attempt, else the LAST attempt.
  B (single-shot control): compress the ORIGINAL doc directly to {25,30,40} words, no clamp.
  C (schedule drop, grok only): unclamped W=40 rounds 1-4, forced W=25 rounds 5-8.

  smoke                                       # 3 grok items all arms + 1 haiku item Arm A
  run --model grok|haiku|gpt [--arm A|B|C] [--limit N]
  score                                       # emits clamped_results.json

Idempotent cache keyed by (model,item,call); Arm-A retries are keyed DISTINCTLY per attempt
(call = "a_compress{r}_try{t}") so a rejected too-short attempt is never replayed as the kept
artifact on resume. Deterministic: temperature 0, fixed item selection, no sampling anywhere.
Hard cap 6000 calls total (all models/arms pooled).
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v2"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "multimodel", "2026-07-03"))
from runner3 import ANS_RE, retained  # noqa: E402
from providers import chat, cost_usd  # noqa: E402

DOMAIN_ITEMS = os.path.join(HERE, "..", "..", "domains", "2026-07-06", "items.jsonl")
RAW = os.path.join(HERE, "responses_raw.jsonl")
RESULTS = os.path.join(HERE, "clamped_results.json")
MODELS = ["grok", "haiku", "gpt"]
W = 40
R = 8
BAND = (36, 44)
MAX_TRIES = 3
B_TARGETS = (25, 30, 40)
DROP_ROUND = 5
W_DROP = 25
N_ITEMS = 40
DOMAINS_USED = ["ops_incident", "clinical_enroll", "ci_release"]
HARD_CAP = 6000  # global across all models and arms (prereg budget section)

# ---- frozen predictors (prereg_clamped.md, fixed 2026-07-09 before any call) ----
H0_POOLED, SIGMA_POOLED = 0.002, 0.48
SIGMA = dict(grok=0.64, haiku=0.54, gpt=0.18)
RHO_BAR = dict(grok=0.931, haiku=0.937, gpt=0.985)  # 2026-07-08 measured, frozen
PRC1_PASS_DECAY, PRC1_FAIL_DECAY = 0.07, 0.20
PRC2_INTERVAL = (0.10, 0.28)
PRC2_CONST_RHO = round(1 - RHO_BAR["grok"], 3)  # 0.069
PRC2_DELTA_GUARD = 0.15
PRC3_TOL, PRC4_TOL, PRC5_TOL = 0.08, 0.01, 0.10
DELTA_CLAMP_TOL = 0.03  # amendment A2: above this mean per-item delta, P-RC-1 -> closer-predictor rule
COST_CAP_USD = 3.00     # amendment A7: enforced at runtime, not just via the call cap

PREDICTIONS = {
    "P-RC-0_clamp_guard": ">=90% of Arm-A kept round-artifacts in [36,44] words, per model",
    "P-RC-1_pure_iteration": "Arm A net decay D=1-S8/S2: D<=0.07 structural pass; D>=0.20 "
                             "structural fail (fitted-geometric band); else revise",
    "P-RC-2_schedule_drop": "Arm C S4->S5 hazard in [0.10,0.28] (structural) vs ~0.069 "
                            "(constant-rho); guard mean delta5 >= 0.15",
    "P-RC-3_state_function": "|S_r(Arm C) - S_direct(interp at L_r)| <= 0.08 at r in {2,4}, grok",
    "P-RC-4_absorbing": "resurrection rate < 1% of value-transitions, every iterated chain",
    "P-RC-5_verdict_eigenvalue_1": "g8 >= g1 - 0.10, every iterated chain",
}

GIST_RE = re.compile(
    r"anomal|exceed|below|out[- ]of[- ]spec|out of range|marginal|elevated|degraded|warning|"
    r"abnormal|deviat|breach|violat|fail|flag|too (high|low)|noncompliant|non-compliant", re.I)
DECISION = " Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED or ANSWER: DENIED."


def comp_sys(kind, w):
    src = "incident file" if kind == "doc" else "case notes"
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following {src} to at most {w} words. A future analyst will need to answer questions "
            f"about this incident, but you do not know which questions. Output only the compressed notes.")


def clamp_sys(kind):
    src = "incident file" if kind == "doc" else "case notes"
    return (f"You are a context compaction engine for an operations assistant. Compress the "
            f"following {src} to between {BAND[0]} and {BAND[1]} words (target {W}). Use the full "
            f"word budget: never fewer than {BAND[0]} words, never more than {BAND[1]}. A future "
            f"analyst will need to answer questions about this incident, but you do not know which "
            f"questions. Output only the compressed notes.")


def retry_user(source, attempt):
    return (source + f"\n\nYour previous compressed notes were {len(attempt.split())} words, "
            f"outside the required {BAND[0]}-{BAND[1]} word band:\n{attempt}\n\nRewrite the "
            f"compressed notes to be between {BAND[0]} and {BAND[1]} words. Output only the "
            f"compressed notes.")


def in_band(s):
    return BAND[0] <= len(s.split()) <= BAND[1]


def load_items():
    all_items = [json.loads(l) for l in open(DOMAIN_ITEMS)]
    out = []
    per = N_ITEMS // len(DOMAINS_USED)
    extra = N_ITEMS - per * len(DOMAINS_USED)
    for di, dom in enumerate(DOMAINS_USED):
        denied = [it for it in all_items if it["domain"] == dom and it["truth"] == "DENIED"]
        take = per + (1 if di < extra else 0)
        out.extend(denied[:take])
    return out


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["model"], r["item"], r["call"])] = r
    return cache


_run_cost = {"usd": None}  # realized cost accumulator (amendment A7)


def api(cache, alias, iid, call, messages):
    key = (alias, iid, call)
    if key in cache:
        return cache[key]["text"]
    if len(cache) + 1 > HARD_CAP:
        sys.exit(f"HARD CAP {HARD_CAP} total calls reached")
    if _run_cost["usd"] is None:
        _run_cost["usd"] = sum(cost_usd(m, r["usage"]) for (m, _i, _c), r in cache.items())
    if _run_cost["usd"] >= COST_CAP_USD:
        sys.exit(f"COST CAP ${COST_CAP_USD:.2f} reached (${_run_cost['usd']:.2f} realized)")
    text, usage = chat(alias, messages)
    rec = dict(model=alias, item=iid, call=call, text=text, usage=usage)
    with open(RAW, "a") as f:
        f.write(json.dumps(rec) + "\n")
    cache[key] = rec
    _run_cost["usd"] += cost_usd(alias, usage)
    return text


def kept_try(cache, alias, iid, r):
    """Kept Arm-A artifact for round r: first in-band attempt, else last executed attempt.
    Same rule at run and score time (prereg). Returns (text, n_tries, in_band)."""
    tries = []
    for t in range(1, MAX_TRIES + 1):
        rec = cache.get((alias, iid, f"a_compress{r}_try{t}"))
        if rec is None:
            break
        tries.append(rec["text"])
        if in_band(rec["text"]):
            break
    if not tries:
        return None, 0, False
    return tries[-1], len(tries), in_band(tries[-1])

# ---------------------------------------------------------------- arms


def run_arm_a(alias, items, cache):
    for n, it in enumerate(items):
        iid = it["id"]
        prev, kind = it["document"], "doc"
        for r in range(1, R + 1):
            attempt = None
            for t in range(1, MAX_TRIES + 1):
                user = prev if t == 1 else retry_user(prev, attempt)
                attempt = api(cache, alias, iid, f"a_compress{r}_try{t}",
                              [{"role": "system", "content": clamp_sys(kind)},
                               {"role": "user", "content": user}])
                if in_band(attempt):
                    break
            summary, _, _ = kept_try(cache, alias, iid, r)
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + summary + "\n\n"
            api(cache, alias, iid, f"a_decision{r}", [{"role": "user", "content": notes + DECISION}])
            prev, kind = summary, "notes"
        if (n + 1) % 10 == 0:
            print(f"  A/{alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)


def run_arm_b(alias, items, cache):
    for n, it in enumerate(items):
        iid = it["id"]
        for w in B_TARGETS:
            s = api(cache, alias, iid, f"b_compress_w{w}",
                    [{"role": "system", "content": comp_sys("doc", w)},
                     {"role": "user", "content": it["document"]}])
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + s + "\n\n"
            api(cache, alias, iid, f"b_decision_w{w}", [{"role": "user", "content": notes + DECISION}])
        if (n + 1) % 20 == 0:
            print(f"  B/{alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)


def run_arm_c(items, cache):
    alias = "grok"
    for n, it in enumerate(items):
        iid = it["id"]
        prev, kind = it["document"], "doc"
        for r in range(1, R + 1):
            w = W if r < DROP_ROUND else W_DROP
            s = api(cache, alias, iid, f"c_compress{r}",
                    [{"role": "system", "content": comp_sys(kind, w)},
                     {"role": "user", "content": prev}])
            notes = it["policy_text"] + "\n\nCompressed case notes:\n" + s + "\n\n"
            api(cache, alias, iid, f"c_decision{r}", [{"role": "user", "content": notes + DECISION}])
            prev, kind = s, "notes"
        if (n + 1) % 10 == 0:
            print(f"  C/{alias} {n + 1}/{len(items)} ({len(cache)} cached)", flush=True)

# ---------------------------------------------------------------- scoring


def mean(xs):
    return round(sum(xs) / len(xs), 4) if xs else None


def norm(s):
    return " ".join(s.lower().split())


def toks(s):
    return set(re.findall(r"[a-z0-9.]+", s.lower()))


def parse_answer(d):
    """Decision parse: the LAST `ANSWER:` match is authoritative (amendment A4; repo battle
    scar #2, last-anchor parsing). Returns (answer_or_None, n_matches, first_last_disagree)."""
    ms = ANS_RE.findall(d)
    if not ms:
        return None, 0, False
    return ms[-1].upper(), len(ms), ms[0].upper() != ms[-1].upper()


def score_chain(items, summ, dec):
    """Generic iterated-chain scorer. summ(it,r)/dec(it,r) -> text or None.
    Complete chains only (amendment A3): items missing any round are counted as
    partial_chains and excluded from every statistic, so S8 and S2 share an item set."""
    rounds = {r: dict(S=[], fail=[], L=[], g=[], gist=[], contain=[], fp=[]) for r in range(1, R + 1)}
    trans = dict(deaths=0, resurrections=0, at_risk=0, absent=0, n=0)
    drop = dict(deaths=0, at_risk=0)  # transition (DROP_ROUND-1)->DROP_ROUND
    delta5 = []
    item_deltas = {}  # iid -> [delta for transitions 1->2 .. 7->8] (amendment A2)
    deaths_per_item = Counter()
    anomalies = dict(unmatched_decisions=0, multi_match_decisions=0,
                     first_last_disagreements=0, empty_summaries=0, partial_chains=0)
    n_scored = 0
    for it in items:
        chain = [summ(it, r) for r in range(1, R + 1)]
        if all(s is None for s in chain):
            continue  # item not run
        if any(s is None for s in chain):
            anomalies["partial_chains"] += 1
            continue  # excluded from all statistics (amendment A3)
        n_scored += 1
        iid = it["id"]
        deaths_per_item[iid] = 0
        item_deltas[iid] = []
        pol = [p for p in it["parameters"] if p["policy"]]
        failp = next((p for p in pol if not p["passes"]), None)
        prev_s = prev_pres = prev_L = None
        for r, s in enumerate(chain, 1):
            if not s.strip():
                anomalies["empty_summaries"] += 1
            pres = [bool(retained(s, p["value"])) for p in pol]
            rounds[r]["S"].append(sum(pres) / len(pol))
            if failp:
                rounds[r]["fail"].append(1.0 if retained(s, failp["value"]) else 0.0)
            L = len(s.split())
            rounds[r]["L"].append(L)
            rounds[r]["gist"].append(1.0 if GIST_RE.search(s) else 0.0)
            d = dec(it, r)
            if d is not None:
                ans, n_m, disagree = parse_answer(d)
                if ans is None:
                    anomalies["unmatched_decisions"] += 1
                if n_m > 1:
                    anomalies["multi_match_decisions"] += 1
                    if disagree:
                        anomalies["first_last_disagreements"] += 1
                rounds[r]["g"].append(1.0 if ans == it["truth"] else 0.0)
            if prev_s is not None:
                tp = toks(s)
                rounds[r]["contain"].append(
                    round(len(tp & toks(prev_s)) / len(tp), 4) if tp else 0.0)
                rounds[r]["fp"].append(1.0 if norm(s) == norm(prev_s) else 0.0)
                for a, b in zip(prev_pres, pres):
                    trans["n"] += 1
                    if a:
                        trans["at_risk"] += 1
                        if not b:
                            trans["deaths"] += 1
                            deaths_per_item[iid] += 1
                            if r == DROP_ROUND:
                                drop["deaths"] += 1
                        if r == DROP_ROUND:
                            drop["at_risk"] += 1
                    else:
                        trans["absent"] += 1
                        if b:
                            trans["resurrections"] += 1
                item_deltas[iid].append(round(max(0.0, 1 - L / prev_L), 4) if prev_L else 0.0)
                if r == DROP_ROUND and prev_L:
                    delta5.append(max(0.0, 1 - L / prev_L))
            prev_s, prev_pres, prev_L = s, pres, L
    curve = {r: {k: mean(v) for k, v in rounds[r].items()} for r in range(1, R + 1)}
    return dict(n_scored=n_scored, curve=curve,
                S_curve=[curve[r]["S"] for r in range(1, R + 1)],
                L_curve=[curve[r]["L"] for r in range(1, R + 1)],
                transitions=trans, drop=drop, delta5_mean=mean(delta5),
                item_deltas=item_deltas,
                death_clustering=dict(sorted(Counter(deaths_per_item.values()).items())),
                resurrection_rate=(round(trans["resurrections"] / trans["n"], 4) if trans["n"] else None),
                anomalies=anomalies)


def interp(points, x):
    """Piecewise-linear in realized length, clamped at endpoints. points: [(L, S)]."""
    pts = sorted(p for p in points if p[0] is not None and p[1] is not None)
    if not pts or x is None:
        return None
    if x <= pts[0][0]:
        return pts[0][1]
    if x >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 if x1 == x0 else round(y0 + (y1 - y0) * (x - x0) / (x1 - x0), 4)


def structural_net(L_curve, sigma):
    """Structural-model S8/S2 from the round-MEAN length trajectory. Understates the
    prediction when per-item lengths oscillate within the band (Jensen; amendment A2) —
    the per-item version below is the one the closer-predictor rule uses."""
    if any(L_curve[r] is None for r in range(1, R)):
        return None
    prod = 1.0
    for r in range(2, R):  # transitions 2->3 .. 7->8 (indices 1..6 of L_curve)
        delta = max(0.0, 1 - L_curve[r] / L_curve[r - 1])
        prod *= 1 - (H0_POOLED + sigma * delta)
    return round(prod, 4)


def structural_net_per_item(item_deltas, sigma):
    """Structural-model S8/S2 at realized per-item deltas: mean over complete-chain items of
    prod over transitions 2->3 .. 7->8 of (1 - h0 - sigma*delta_item_r). (Amendment A2.)"""
    vals = []
    for deltas in item_deltas.values():  # deltas[0] is 1->2; [1:] are 2->3 .. 7->8
        prod = 1.0
        for d in deltas[1:]:
            prod *= 1 - (H0_POOLED + sigma * d)
        vals.append(prod)
    return mean(vals)


def do_score():
    items = load_items()
    cache = load_cache()
    if not cache:
        sys.exit("no cached responses yet; run the arms first")
    # ---- tokens / cost, per model and per (model, arm) ----
    tok = defaultdict(lambda: dict(prompt=0, completion=0))
    tok_arm = defaultdict(lambda: dict(prompt=0, completion=0))
    n_calls = Counter()
    for (m, _i, c), rec in cache.items():
        for k in ("prompt", "completion"):
            tok[m][k] += rec["usage"][k]
            tok_arm[(m, c[0])][k] += rec["usage"][k]
        n_calls[m] += 1
        n_calls[f"{m}/{c[0].upper()}"] += 1
    cost = {m: round(cost_usd(m, tok[m]), 4) for m in tok}
    cost_by_arm = {f"{m}/{a.upper()}": round(cost_usd(m, t), 4) for (m, a), t in tok_arm.items()}

    out = {"design": dict(W=W, R=R, band=BAND, max_tries=MAX_TRIES, b_targets=B_TARGETS,
                          drop_round=DROP_ROUND, w_drop=W_DROP, n_items=len(items),
                          domains=DOMAINS_USED, predictions=PREDICTIONS,
                          frozen_predictors=dict(
                              structural=dict(h0=H0_POOLED, sigma_pooled=SIGMA_POOLED,
                                              sigma_per_model=SIGMA),
                              fitted_geometric=dict(rho_bar=RHO_BAR)))}

    # ---- Arm A ----
    arm_a = {}
    for alias in MODELS:
        ch = score_chain(
            items,
            lambda it, r, a=alias: kept_try(cache, a, it["id"], r)[0],
            lambda it, r, a=alias: (cache.get((a, it["id"], f"a_decision{r}")) or {}).get("text"))
        if ch["n_scored"] == 0 and ch["anomalies"]["partial_chains"] == 0:
            continue
        att_hist, ib, ib_round = Counter(), [], {r: [] for r in range(1, R + 1)}
        for it in items:
            for r in range(1, R + 1):
                text, t, band_ok = kept_try(cache, alias, it["id"], r)
                if text is None:
                    continue
                att_hist[t] += 1
                ib.append(1.0 if band_ok else 0.0)
                ib_round[r].append(1.0 if band_ok else 0.0)
        ch["in_band_frac"] = mean(ib)
        ch["in_band_per_round"] = {r: mean(v) for r, v in ib_round.items()}  # amendment A5
        ch["kept_artifacts_n"] = len(ib)
        ch["attempts_hist"] = dict(sorted(att_hist.items()))
        ch["mean_attempts"] = mean([t for t, n in att_hist.items() for _ in range(n)])
        ideltas = ch["item_deltas"]
        post = [d for ds in ideltas.values() for d in ds[1:]]  # transitions 2->3 .. 7->8
        ch["delta_bar_per_item"] = mean(post)  # amendment A2 adjudication statistic
        ch["delta_per_transition"] = [
            dict(transition=f"{k + 1}->{k + 2}",
                 mean=mean([ds[k] for ds in ideltas.values()]),
                 max=(round(max(ds[k] for ds in ideltas.values()), 4) if ideltas else None))
            for k in range(R - 1)]
        S = ch["S_curve"]
        ch["rho_ratios"] = [round(S[r] / S[r - 1], 4)
                            if S[r] is not None and S[r - 1] else None for r in range(1, R)]
        s2, s8 = S[1], S[R - 1]
        ch["S8_over_S2"] = round(s8 / s2, 4) if s8 is not None and s2 not in (None, 0) else None
        ch["net_decay"] = round(1 - ch["S8_over_S2"], 4) if ch["S8_over_S2"] is not None else None
        arm_a[alias] = ch

    # ---- Arm B ----
    arm_b = {}
    for alias in MODELS:
        per_t = {}
        for w in B_TARGETS:
            Ss, Ls, gs, unm, multi, disg = [], [], [], 0, 0, 0
            for it in items:
                rec = cache.get((alias, it["id"], f"b_compress_w{w}"))
                if rec is None:
                    continue
                s = rec["text"]
                pol = [p for p in it["parameters"] if p["policy"]]
                Ss.append(sum(bool(retained(s, p["value"])) for p in pol) / len(pol))
                Ls.append(len(s.split()))
                d = (cache.get((alias, it["id"], f"b_decision_w{w}")) or {}).get("text")
                if d is not None:
                    ans, n_m, disagree = parse_answer(d)
                    if ans is None:
                        unm += 1
                    if n_m > 1:
                        multi += 1
                        if disagree:
                            disg += 1
                    gs.append(1.0 if ans == it["truth"] else 0.0)
            if Ss:
                per_t[w] = dict(n=len(Ss), S=mean(Ss), L=mean(Ls), g=mean(gs),
                                unmatched_decisions=unm, multi_match_decisions=multi,
                                first_last_disagreements=disg)
        if per_t:
            arm_b[alias] = per_t

    # ---- Arm C ----
    arm_c = score_chain(
        items,
        lambda it, r: (cache.get(("grok", it["id"], f"c_compress{r}")) or {}).get("text"),
        lambda it, r: (cache.get(("grok", it["id"], f"c_decision{r}")) or {}).get("text"))
    if arm_c["n_scored"]:
        d = arm_c["drop"]
        arm_c["drop_hazard"] = round(d["deaths"] / d["at_risk"], 4) if d["at_risk"] else None
        S = arm_c["S_curve"]
        arm_c["one_minus_S5_over_S4"] = (round(1 - S[DROP_ROUND - 1] / S[DROP_ROUND - 2], 4)
                                         if S[DROP_ROUND - 1] is not None
                                         and S[DROP_ROUND - 2] not in (None, 0) else None)

    # ---- P-RC-0 ----
    prc0 = {m: dict(in_band_frac=arm_a[m]["in_band_frac"],
                    passed=bool(arm_a[m]["in_band_frac"] is not None
                                and arm_a[m]["in_band_frac"] >= 0.90)) for m in arm_a}
    applicable = [m for m in arm_a if prc0[m]["passed"]]

    # ---- P-RC-1 + predictor table ----
    prc1, table = {}, []
    for m in arm_a:
        D = arm_a[m]["net_decay"]
        if D is None:
            band = "insufficient_data"
        elif D <= PRC1_PASS_DECAY:
            band = "pass"
        elif D >= PRC1_FAIL_DECAY:
            band = "fail"
        else:
            band = "revise"
        meas = arm_a[m]["S8_over_S2"]
        d_bar = arm_a[m]["delta_bar_per_item"]
        s_per_item = structural_net_per_item(arm_a[m]["item_deltas"], SIGMA[m])
        f_pred = round(RHO_BAR[m] ** 6, 4)
        # amendment A2: if the clamp did not hold delta ~ 0, adjudicate by closer predictor
        if band == "insufficient_data":
            headline, rule = band, "band"
        elif d_bar is not None and d_bar > DELTA_CLAMP_TOL:
            ds, df = abs(meas - s_per_item), abs(meas - f_pred)
            headline = "pass" if ds < df else ("fail" if df < ds else "revise")
            rule = f"closer_predictor (delta_bar {d_bar} > {DELTA_CLAMP_TOL})"
        else:
            headline, rule = band, "band"
        ratios = arm_a[m]["rho_ratios"][1:]  # transitions 2->3 .. 7->8
        sub_98 = (all(x is not None and x >= 0.98 for x in ratios) if ratios else None)
        prc1[m] = dict(net_decay=D, S8_over_S2=meas, band_outcome=band,
                       outcome_headline=headline, adjudication_rule=rule,
                       delta_bar_per_item=d_bar,
                       structural_per_item_at_realized_delta=s_per_item,
                       fitted_geometric=f_pred,
                       applicable=m in applicable,
                       subcheck_all_rounds_ge_098=sub_98,
                       subcheck_S8_over_S2_ge_087=(meas is not None and meas >= 0.87))
        table.append(dict(
            model=m, arm="A", quantity="S8/S2",
            measured=meas,
            structural_clamped_point=round((1 - H0_POOLED) ** 6, 4),
            structural_given_realized_L_pooled=structural_net(arm_a[m]["L_curve"], SIGMA_POOLED),
            structural_given_realized_L_per_model=structural_net(arm_a[m]["L_curve"], SIGMA[m]),
            structural_per_item_pooled=structural_net_per_item(arm_a[m]["item_deltas"], SIGMA_POOLED),
            structural_per_item_per_model=s_per_item,
            fitted_geometric=f_pred))
    primary_applicable = [m for m in ("grok", "haiku") if m in applicable]  # amendment A1
    prc1_overall = dict(
        pass_all_applicable=bool(applicable) and all(
            prc1[m]["outcome_headline"] == "pass" for m in applicable),
        primary_discriminators_applicable=primary_applicable,
        primary_discriminators_pass=(all(prc1[m]["outcome_headline"] == "pass"
                                         for m in primary_applicable)
                                     if primary_applicable else None),
        per_model={m: prc1[m]["outcome_headline"] for m in prc1})

    # ---- P-RC-2 ----
    prc2 = dict(outcome="insufficient_data")
    if arm_c["n_scored"]:
        d5 = arm_c["delta5_mean"]
        hz = arm_c["drop_hazard"]
        struct_pt = round(H0_POOLED + SIGMA["grok"] * d5, 4) if d5 is not None else None
        guard = bool(d5 is not None and d5 >= PRC2_DELTA_GUARD)
        if hz is None or d5 is None:
            outcome = "insufficient_data"
        elif not guard:
            outcome = "inapplicable"
        elif PRC2_INTERVAL[0] <= hz <= PRC2_INTERVAL[1]:
            outcome = "pass"
        elif hz < PRC2_INTERVAL[0]:
            outcome = "fail"  # constant-rho favored
        else:
            outcome = "neither_overshoot"
        prc2 = dict(delta5_mean=d5, guard_delta5_ge_015=guard, drop_hazard=hz,
                    one_minus_S5_over_S4=arm_c["one_minus_S5_over_S4"],
                    structural_interval=PRC2_INTERVAL,
                    structural_point_at_realized_delta=struct_pt,
                    constant_rho_point=PRC2_CONST_RHO, outcome=outcome)
        table.append(dict(model="grok", arm="C", quantity="drop-round hazard (S4->S5)",
                          measured=hz, structural_point_at_realized_delta=struct_pt,
                          structural_interval=PRC2_INTERVAL,
                          fitted_geometric=PRC2_CONST_RHO))

    # ---- P-RC-3 ----
    prc3 = dict(passed=None)
    if arm_c["n_scored"] and "grok" in arm_b:
        pts = [(arm_b["grok"][w]["L"], arm_b["grok"][w]["S"]) for w in B_TARGETS if w in arm_b["grok"]]
        checks = {}
        for r in (2, 4):
            Lr, Sr = arm_c["curve"][r]["L"], arm_c["curve"][r]["S"]
            Sd = interp(pts, Lr)
            checks[f"round{r}"] = dict(
                L=Lr, S_iterated=Sr, S_direct_interp=Sd,
                abs_diff=(round(abs(Sr - Sd), 4) if None not in (Sr, Sd) else None))
        diffs = [c["abs_diff"] for c in checks.values()]
        prc3 = dict(direct_points=pts, checks=checks,
                    passed=(all(d is not None and d <= PRC3_TOL for d in diffs)
                            if all(d is not None for d in diffs) else None))

    # ---- P-RC-4 / P-RC-5 ----
    chains = {f"A/{m}": arm_a[m] for m in arm_a}
    if arm_c["n_scored"]:
        chains["C/grok"] = arm_c
    prc4 = dict(per_chain={k: c["resurrection_rate"] for k, c in chains.items()},
                passed=all(c["resurrection_rate"] is not None and c["resurrection_rate"] < PRC4_TOL
                           for c in chains.values()) if chains else None)
    prc5_detail = {}
    for k, c in chains.items():
        g1, g8 = c["curve"][1]["g"], c["curve"][R]["g"]
        prc5_detail[k] = dict(g1=g1, g8=g8,
                              passed=(g8 >= g1 - PRC5_TOL if None not in (g1, g8) else None))
    prc5_vals = [v["passed"] for v in prc5_detail.values()]
    prc5 = dict(per_chain=prc5_detail,
                passed=(None if (not prc5_vals or any(v is None for v in prc5_vals))
                        else all(prc5_vals)))

    # ---- verdict (logic fixed in prereg; headline rule per amendment A1) ----
    p2o = prc2["outcome"]
    headline_applicable = bool(primary_applicable)
    structural_upheld = bool(headline_applicable and prc1_overall["pass_all_applicable"]
                             and p2o in ("pass", "inapplicable"))
    fitted_upheld = bool(set(primary_applicable) == {"grok", "haiku"}
                         and all(prc1[m]["outcome_headline"] == "fail" for m in ("grok", "haiku"))
                         and p2o in ("fail", "inapplicable"))
    verdict = dict(headline_applicable=headline_applicable,
                   structural_upheld=structural_upheld, fitted_geometric_upheld=fitted_upheld,
                   mixed=bool(headline_applicable and not (structural_upheld or fitted_upheld)),
                   applicable_models=applicable,
                   note=(None if headline_applicable else
                         "no primary discriminator (grok, haiku) passed P-RC-0; "
                         "per-model report only (amendment A1)"))

    # ---- exploratory (labeled; no confirmatory weight) ----
    exploratory = dict(label="EXPLORATORY")
    if "haiku" in arm_a:
        exploratory["haiku_fixed_point_early_vs_late"] = dict(
            fp_2_to_3=arm_a["haiku"]["curve"][3]["fp"], fp_7_to_8=arm_a["haiku"]["curve"][R]["fp"])
    exploratory["fixed_point_curves"] = {
        k: [c["curve"][r]["fp"] for r in range(2, R + 1)] for k, c in chains.items()}
    exploratory["containment_curves"] = {
        k: [c["curve"][r]["contain"] for r in range(2, R + 1)] for k, c in chains.items()}
    plateaus = {}
    if arm_c["n_scored"]:
        plateaus["armC_grok_S4_vs_0.767"] = dict(measured=arm_c["curve"][4]["S"], reference=0.767)
    if "gpt" in arm_a:
        plateaus["armA_gpt_S8_vs_0.883"] = dict(measured=arm_a["gpt"]["curve"][R]["S"], reference=0.883)
    if "haiku" in arm_a:
        plateaus["armA_haiku_S8_vs_0.542_non_comparable_under_structural"] = dict(
            measured=arm_a["haiku"]["curve"][R]["S"], reference=0.542)
    exploratory["plateaus"] = plateaus

    anomalies = dict(
        arm_a={m: arm_a[m]["anomalies"] for m in arm_a},
        arm_c=arm_c["anomalies"],
        arm_b_unmatched={m: {w: t["unmatched_decisions"] for w, t in per.items()}
                         for m, per in arm_b.items()})

    out.update(arm_A=arm_a, arm_B=arm_b, arm_C=(arm_c if arm_c["n_scored"] else None),
               predictions_evaluated={"P-RC-0": prc0, "P-RC-1": dict(prc1_overall, per_model_detail=prc1),
                                      "P-RC-2": prc2, "P-RC-3": prc3, "P-RC-4": prc4, "P-RC-5": prc5},
               predictor_table=table, verdict=verdict, exploratory=exploratory,
               anomalies=anomalies, n_calls=dict(n_calls), total_calls=len(cache),
               cost_usd=cost, cost_usd_by_arm=cost_by_arm,
               total_cost_usd=round(sum(cost.values()), 4))
    json.dump(out, open(RESULTS, "w"), indent=1, default=str)

    for m in arm_a:
        a = arm_a[m]
        print(f"\n=== Arm A {m} === (n={a['n_scored']}, partial={a['anomalies']['partial_chains']}, "
              f"in-band {a['in_band_frac']}, attempts {a['attempts_hist']})")
        print(f"  S: {a['S_curve']}")
        print(f"  L: {a['L_curve']}")
        print(f"  delta_bar_per_item={a['delta_bar_per_item']}  "
              f"struct_per_item={prc1[m]['structural_per_item_at_realized_delta']}")
        print(f"  S8/S2={a['S8_over_S2']}  net_decay={a['net_decay']}  "
              f"fitted-geometric pred {round(RHO_BAR[m] ** 6, 4)}  "
              f"P-RC-0 {'PASS' if prc0[m]['passed'] else 'FAIL'}  "
              f"P-RC-1 {prc1[m]['outcome_headline'].upper()} "
              f"(band {prc1[m]['band_outcome']}, rule {prc1[m]['adjudication_rule']})")
    if arm_c["n_scored"]:
        print(f"\n=== Arm C grok === (n={arm_c['n_scored']})")
        print(f"  S: {arm_c['S_curve']}")
        print(f"  L: {arm_c['L_curve']}")
        print(f"  delta5={prc2.get('delta5_mean')}  hazard={prc2.get('drop_hazard')}  "
              f"P-RC-2 {prc2['outcome'].upper()}")
    for name, res in (("P-RC-3", prc3.get("passed")), ("P-RC-4", prc4.get("passed")),
                      ("P-RC-5", prc5.get("passed"))):
        print(f"  {name}: {'PASS' if res else 'FAIL' if res is not None else 'n/a'}")
    print(f"\nverdict: {json.dumps(verdict)}")
    print(f"calls: {len(cache)}  cost: {json.dumps(cost)}  total ${out['total_cost_usd']}")
    print(f"wrote {RESULTS}")

# ---------------------------------------------------------------- smoke / main


def do_smoke():
    items = load_items()[:3]
    cache = load_cache()
    print("smoke: grok arms A+B+C on 3 items, haiku Arm A on 1 item")
    run_arm_a("grok", items, cache)
    run_arm_b("grok", items, cache)
    run_arm_c(items, cache)
    run_arm_a("haiku", items[:1], cache)
    for alias, its, arms in (("grok", items, "ABC"), ("haiku", items[:1], "A")):
        for it in its:
            print(f"\n--- {alias} {it['id']} truth={it['truth']} failing={it['failing_param']!r}")
            for r in range(1, R + 1):
                kept, n_tries, band_ok = kept_try(cache, alias, it["id"], r)
                for t in range(1, n_tries + 1):
                    s = cache[(alias, it["id"], f"a_compress{r}_try{t}")]["text"]
                    print(f"  A r{r} try{t} ({len(s.split())}w{', IN-BAND' if in_band(s) else ''}): "
                          f"{s.strip()}")
                d = (cache.get((alias, it["id"], f"a_decision{r}")) or {}).get("text", "")
                print(f"  A r{r} kept=try{n_tries} in_band={band_ok}  dec: {d.strip()[:60]}")
            if "B" in arms:
                for w in B_TARGETS:
                    s = cache[(alias, it["id"], f"b_compress_w{w}")]["text"]
                    d = (cache.get((alias, it["id"], f"b_decision_w{w}")) or {}).get("text", "")
                    print(f"  B w{w} ({len(s.split())}w): {s.strip()}")
                    print(f"     dec: {d.strip()[:60]}")
            if "C" in arms:
                for r in range(1, R + 1):
                    s = cache[(alias, it["id"], f"c_compress{r}")]["text"]
                    d = (cache.get((alias, it["id"], f"c_decision{r}")) or {}).get("text", "")
                    print(f"  C r{r} W={W if r < DROP_ROUND else W_DROP} ({len(s.split())}w): {s.strip()}")
                    print(f"     dec: {d.strip()[:60]}")
    print(f"\nsmoke done ({len(cache)} calls cached)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "smoke", "score"])
    ap.add_argument("--model", choices=MODELS)
    ap.add_argument("--arm", choices=["A", "B", "C"])
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cmd == "score":
        do_score()
        return
    if a.cmd == "smoke":
        do_smoke()
        return
    if not a.model:
        sys.exit("run requires --model")
    if a.arm == "C" and a.model != "grok":
        sys.exit("Arm C is grok-only (prereg)")
    items = load_items()
    if a.limit:
        items = items[:a.limit]
    cache = load_cache()
    arms = a.arm or ("ABC" if a.model == "grok" else "AB")
    if "A" in arms:
        run_arm_a(a.model, items, cache)
    if "B" in arms:
        run_arm_b(a.model, items, cache)
    if "C" in arms and a.model == "grok":
        run_arm_c(items, cache)
    print(f"{a.model} arms {arms} done ({len(items)} items, {len(cache)} calls cached)")


if __name__ == "__main__":
    main()
