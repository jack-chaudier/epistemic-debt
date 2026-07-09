#!/usr/bin/env python3
"""EXPLORATORY logit-lens probe (pod-side, transformers+peft, bf16 1.7B on one 4090).

On Student-V's fail-open cells (ablated DENIED items it answered APPROVED under abl_bare),
teacher-force the prompt + "ANSWER:" and read the per-layer (APPROVED - DENIED) next-token
logit gap via the logit lens (final norm + lm_head applied to every layer's hidden state).
Classify per item: computed-but-outvoted (any second-half layer with DENIED > APPROVED) vs
never-computed. Reference trajectories: sj and base on the SAME items. Writes lens_results.json.
No thresholds — exploratory by prereg."""
import json
import os

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "Qwen/Qwen3-1.7B"
ADAPTERS = dict(sv="/workspace/student_V/final", sj="/workspace/student_J/final")
MAX_ITEMS = 60

DECISION = (" Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED "
            "or ANSWER: DENIED.")

tok = AutoTokenizer.from_pretrained(BASE)
APPROVED_ID = tok.encode(" APPROVED", add_special_tokens=False)[0]
DENIED_ID = tok.encode(" DENIED", add_special_tokens=False)[0]
assert APPROVED_ID != DENIED_ID

items = {it["id"]: it for it in map(json.loads, open(os.path.join(HERE, "sections_items.jsonl")))}
raw = {}
for l in open(os.path.join(HERE, "responses_raw.jsonl")):
    r = json.loads(l)
    raw[(r["model"], r["item"], r["call"])] = r["text"]

# V's fail-open cells: ablated DENIED items answered APPROVED under abl_bare
fail_open = []
for it in items.values():
    if it["truth"] != "DENIED":
        continue
    t = raw.get(("sv", it["id"], "abl_bare"), "")
    if "ANSWER: APPROVED" in t.upper().replace("**", ""):
        fail_open.append(it)
fail_open = fail_open[:MAX_ITEMS]
print(f"{len(fail_open)} fail-open cells probed")


def gaps_for(model, it):
    msgs = [dict(role="user", content=it["policy_text"] + "\n\nCase file:\n"
                 + it["document_ablated"] + "\n\n" + DECISION.strip())]
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True,
                                     enable_thinking=False) + "ANSWER:"
    ids = tok(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model(**ids, output_hidden_states=True)
    core = model.get_base_model() if hasattr(model, "get_base_model") else model
    lm = core.get_output_embeddings().weight
    norm = core.model.norm
    g = []
    for h in out.hidden_states[1:]:
        v = norm(h[0, -1]).to(lm.dtype)
        logits = lm @ v
        g.append(round(float(logits[APPROVED_ID] - logits[DENIED_ID]), 3))
    return g


results = {}
base_model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16,
                                                  device_map="cuda")
for name in ("base", "sv", "sj"):
    model = base_model if name == "base" else PeftModel.from_pretrained(base_model, ADAPTERS[name])
    rows = []
    for it in fail_open:
        g = gaps_for(model, it)
        half = len(g) // 2
        crossings = [i for i, x in enumerate(g) if x < 0]
        rows.append(dict(item=it["id"], final_gap=g[-1],
                         second_half_denied_layers=[i for i in crossings if i >= half],
                         any_denied_layer=bool(crossings), gaps=g))
    n = len(rows)
    outvoted = sum(1 for r in rows if r["second_half_denied_layers"] and r["final_gap"] > 0)
    results[name] = dict(
        n=n, final_approve=sum(r["final_gap"] > 0 for r in rows),
        computed_but_outvoted=outvoted,
        never_computed=sum(1 for r in rows if not r["any_denied_layer"] and r["final_gap"] > 0),
        rows=rows)
    print(f"{name}: n={n} final_approve={results[name]['final_approve']} "
          f"outvoted={outvoted} never_computed={results[name]['never_computed']}")
    if name != "base":
        model = model.unload()  # strip adapter, restore clean base for the next pass

json.dump(results, open(os.path.join(HERE, "lens_results.json"), "w"), indent=1)
print("wrote lens_results.json")
