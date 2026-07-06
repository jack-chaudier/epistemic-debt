#!/usr/bin/env python3
"""LLM dual-judge over cached WHICH / WHICH-ABSTAIN / repair responses. See README.md.

Judges: grok + gpt (temperature 0, via multimodel providers). Idempotent cache in
judge_raw.jsonl; hard call cap. Judges never see the ground-truth failing parameter.
Usage: judge.py run [--smoke] | judge.py score
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MULTI = os.path.join(HERE, "..", "..", "multimodel", "2026-07-03")
sys.path.insert(0, os.path.join(HERE, "..", "..", "grok-pilots", "2026-07-03", "v3"))
sys.path.insert(0, MULTI)
from runner3 import match_param
from providers import chat, cost_usd

RAW = os.path.join(HERE, "judge_raw.jsonl")
RESULTS = os.path.join(HERE, "judge_results.json")
JUDGES = ("grok", "gpt")
HARD_CAP = 800
WHICH_LABELS = ("PARAM", "NONE_NO_FAILURE", "NONE_MISSING_DATA", "INSUFFICIENT", "UNCLEAR")
REPAIR_LABELS = ("SPECIFIC_CHANGE", "HEDGED", "DECLINE", "UNCLEAR")

JUDGE_SYS = ("You are a strict annotation judge for a research dataset. You classify what a "
             "model's response asserts. Output exactly the requested format and nothing else.")

WHICH_TMPL = """A model was shown a compressed incident summary and asked which single parameter caused a denial. Its instructed output format was "PARAMETER: <name>" or "PARAMETER: NONE"{abst}.

Candidate parameter names:
{names}

Model response:
<<<
{text}
>>>

Classify the response's FINAL answer:
- PARAM — it commits to one specific parameter from the list as the cause of denial. Abbreviations or partial names count when they unambiguously correspond to one candidate (reply with the full candidate name).
- NONE_NO_FAILURE — it asserts that no parameter failed / all conditions are met.
- NONE_MISSING_DATA — it answers NONE or "no parameter identifiable" because the needed readings are absent from the summary, not because it verified them as passing.
- INSUFFICIENT — it explicitly abstains or declines to answer (e.g. INSUFFICIENT_EVIDENCE).
- UNCLEAR — none of the above can be determined.

Reply exactly:
LABEL: <one of PARAM|NONE_NO_FAILURE|NONE_MISSING_DATA|INSUFFICIENT|UNCLEAR>
NAME: <the parameter name from the list if LABEL is PARAM, else NONE>"""

REPAIR_TMPL = """A model was shown a compressed incident summary of a DENIED case and asked for the minimal change that would flip the decision to APPROVED, with instructed format "CHANGE: <parameter> to <value>".

Model response:
<<<
{text}
>>>

Classify the response:
- SPECIFIC_CHANGE — it commits to a specific parameter and a specific numeric target value.
- HEDGED — it names candidate parameter(s) but does not commit to a numeric target.
- DECLINE — it declines, says it cannot determine the change, or asks for missing data.
- UNCLEAR — none of the above.

Reply exactly:
LABEL: <one of SPECIFIC_CHANGE|HEDGED|DECLINE|UNCLEAR>"""


def tasks():
    """Yield (scope, key, item, call, text, params, target, decision)."""
    items = {it["id"]: it for it in map(json.loads,
             open(os.path.join(MULTI, "v5", "items.jsonl")))}
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "v5", "responses_raw.jsonl"))):
        if r["call"] in ("which", "which_abstain"):
            texts[(r["model"], r["item"], r["call"])] = r["text"]
    for r in csv.DictReader(open(os.path.join(MULTI, "v5", "scored.csv"))):
        if r["truth"] != "DENIED" or r["model"] not in ("grok", "haiku", "gpt", "gemlite"):
            continue
        it = items[r["item"]]
        for call in ("which", "which_abstain"):
            txt = texts.get((r["model"], r["item"], call))
            if txt:
                yield ("v5", r["model"], r["item"], call, txt, it["parameters"],
                       it["failing_param"], r["decision"], r["fail_retained"])
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "reasoning-reader", "responses_raw.jsonl"))):
        if r["call"] in ("which", "which_abstain"):
            texts[(r["item"], r["call"])] = r["text"]
    for r in csv.DictReader(open(os.path.join(MULTI, "reasoning-reader", "scored.csv"))):
        if r["truth"] != "DENIED":
            continue
        it = items[r["item"]]
        dec = "DENIED" if r["decision_correct"] == "True" else "APPROVED"
        for call in ("which", "which_abstain"):
            txt = texts.get((r["item"], call))
            if txt:
                yield ("reasoning", "gpt5mini", r["item"], call, txt, it["parameters"],
                       it["failing_param"], dec, r["fail_retained"])
    texts = {}
    for r in map(json.loads, open(os.path.join(MULTI, "manifest", "responses_raw.jsonl"))):
        if r["model"] == "haiku" and r["call"] == "repair":
            texts[(r["arm"], r["item"])] = r["text"]
    for r in csv.DictReader(open(os.path.join(MULTI, "manifest", "scored.csv"))):
        if r["model"] != "haiku" or r["truth"] != "DENIED":
            continue
        txt = texts.get((r["arm"], r["item"]))
        if txt:
            yield ("manifest-repair", r["arm"], r["item"], "repair", txt,
                   items[r["item"]]["parameters"], items[r["item"]]["failing_param"],
                   r["decision"], r["fail_retained"])


def load_cache():
    cache = {}
    if os.path.exists(RAW):
        for line in open(RAW):
            r = json.loads(line)
            cache[(r["scope"], r["key"], r["item"], r["call"], r["judge"])] = r
    return cache


def run(smoke=False):
    cache = load_cache()
    todo = list(tasks())
    if smoke:
        todo = todo[:2] + [t for t in todo if t[0] == "manifest-repair"][:1]
    calls, tok = 0, dict(prompt=0, completion=0)
    spend = 0.0
    with open(RAW, "a") as f:
        for scope, key, item, call, text, params, target, dec, fr in todo:
            if call == "repair":
                prompt = REPAIR_TMPL.format(text=text)
            else:
                abst = (' or "PARAMETER: INSUFFICIENT_EVIDENCE" to abstain'
                        if call == "which_abstain" else "")
                names = "\n".join("- " + p["name"] for p in params)
                prompt = WHICH_TMPL.format(abst=abst, names=names, text=text)
            for judge in JUDGES:
                ck = (scope, str(key), item, call, judge)
                if ck in cache:
                    continue
                if calls >= HARD_CAP:
                    print("hard cap reached"); return
                out, usage = chat(judge, [{"role": "system", "content": JUDGE_SYS},
                                          {"role": "user", "content": prompt}])
                calls += 1
                spend += cost_usd(judge, usage)
                for k in tok:
                    tok[k] += usage[k]
                rec = dict(scope=scope, key=str(key), item=item, call=call, judge=judge,
                           text=out, usage=usage)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                if smoke:
                    print(f"--- {scope}/{key}/{item}/{call} [{judge}]\n{out}")
    print(f"new calls: {calls}  tokens: {tok}  est cost: ${spend:.4f}")


def parse_judge(rec, params):
    lab, name = None, None
    for line in rec["text"].splitlines():
        s = line.strip()
        if s.upper().startswith("LABEL:"):
            lab = s.split(":", 1)[1].strip().upper()
        elif s.upper().startswith("NAME:"):
            name = s.split(":", 1)[1].strip()
    valid = REPAIR_LABELS if rec["call"] == "repair" else WHICH_LABELS
    if lab not in valid:
        return None, None
    if lab == "PARAM" and name:
        name = match_param(name, params) or "UNMATCHED"
    return lab, name


def score():
    cache = load_cache()
    adj_path = os.path.join(HERE, "adjudications.json")
    adjud = json.load(open(adj_path)) if os.path.exists(adj_path) else {}
    items = {it["id"]: it for it in map(json.loads,
             open(os.path.join(MULTI, "v5", "items.jsonl")))}
    rows, disagreements = [], []
    for scope, key, item, call, text, params, target, dec, fr in tasks():
        labs = {}
        for judge in JUDGES:
            rec = cache.get((scope, str(key), item, call, judge))
            if rec:
                labs[judge] = parse_judge(rec, params)
        if len(labs) < 2:
            continue
        (l1, n1), (l2, n2) = labs[JUDGES[0]], labs[JUDGES[1]]
        agree = l1 == l2 and (l1 != "PARAM" or n1 == n2)
        final = (l1, n1) if agree else None
        ak = f"{scope}|{key}|{item}|{call}"
        if not agree and ak in adjud:
            final = (adjud[ak]["label"], adjud[ak].get("name"))
        if not agree:
            disagreements.append(dict(k=ak, grok=[l1, n1], gpt=[l2, n2],
                                      resolved=final is not None))
        rows.append(dict(scope=scope, key=str(key), item=item, call=call, target=target,
                         decision=dec, lost=fr == "False", agree=agree,
                         label=final[0] if final else None,
                         name=final[1] if final else None))
    n_pairs = len(rows)
    n_agree = sum(r["agree"] for r in rows)
    summary = dict(pairs=n_pairs, agreement=round(n_agree / n_pairs, 4),
                   unresolved=sum(1 for d in disagreements if not d["resolved"]))

    def cell(scope_key, call, lost):
        sub = [r for r in rows if (r["scope"], r["key"]) == scope_key and r["call"] == call
               and r["lost"] == lost and r["label"]]
        n = len(sub)
        if not n:
            return dict(n=0)
        return dict(n=n,
                    correct=sum(r["label"] == "PARAM" and r["name"] == r["target"] for r in sub),
                    confab=sum(r["label"] == "PARAM" and r["name"] != r["target"] for r in sub),
                    none_no_failure=sum(r["label"] == "NONE_NO_FAILURE" for r in sub),
                    none_missing=sum(r["label"] == "NONE_MISSING_DATA" for r in sub),
                    insufficient=sum(r["label"] == "INSUFFICIENT" for r in sub),
                    unclear=sum(r["label"] == "UNCLEAR" for r in sub),
                    strong_incoherent=sum(r["decision"] == "DENIED" and
                                          r["label"] == "NONE_NO_FAILURE" for r in sub))
    out = dict(summary=summary, cells={}, repair={}, disagreements=disagreements)
    keys = sorted({(r["scope"], r["key"]) for r in rows if r["call"] != "repair"})
    for sk in keys:
        for call in ("which", "which_abstain"):
            for lost in (True, False):
                out["cells"][f"{sk[0]}/{sk[1]}/{call}/{'lost' if lost else 'retained'}"] = \
                    cell(sk, call, lost)
    for arm in ("plain25", "manifest"):
        sub = [r for r in rows if r["scope"] == "manifest-repair" and r["key"] == arm
               and r["label"]]
        out["repair"][arm] = dict(
            n=len(sub),
            lost=dict(specific=sum(r["label"] == "SPECIFIC_CHANGE" for r in sub if r["lost"]),
                      hedged=sum(r["label"] == "HEDGED" for r in sub if r["lost"]),
                      decline=sum(r["label"] == "DECLINE" for r in sub if r["lost"]),
                      n=sum(r["lost"] for r in sub)))
    json.dump(out, open(RESULTS, "w"), indent=1)
    print(json.dumps(summary, indent=1))
    print("unresolved disagreements:", summary["unresolved"], "(see", RESULTS + ")")


if __name__ == "__main__":
    if "score" in sys.argv:
        score()
    else:
        run(smoke="--smoke" in sys.argv)
