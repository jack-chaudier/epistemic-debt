#!/usr/bin/env python3
"""Distill-parity campaign runner — teacher traces + every eval battery, against a local
vLLM OpenAI-compatible server (pod-side). Stdlib only.

    python3 runner.py smoke                                   # local, no server: print 3 items'
                                                              # prompts per battery for spot-reading
    python3 runner.py traces     --model teacher              # teacher_v + teacher_j over train pool
    python3 runner.py parity     --model sv --adapter ...     # parity gauge decision probes
    python3 runner.py dev        --model sv                   # dev-slice decision probes
    python3 runner.py capability --model sv                   # 250 GSM8K + 250 MMLU
    python3 runner.py delta      --model sv                   # dissociation battery (15w blind)
    python3 runner.py arm3a      --model sv                   # FULL-DOC counterfactual (headline)
    python3 runner.py arm3b      --model sv                   # compressed-artifact counterfactual
    python3 runner.py realdoc    --model sv                   # row-31 NTSB corpus battery

Contract (frozen prereg d24e198): temperature 0; Qwen3 thinking disabled on EVERY request via
chat_template_kwargs {"enable_thinking": false}; any residual <think> block stripped before the
raw record is written; idempotent cache keyed (model, item, call, variant=0); hard call cap.
Raw records append to teacher_raw.jsonl (traces) / responses_raw.jsonl (all eval batteries).

Arm 3a decision probes request the bare ANSWER: line from every model — format-neutral across
Student-V and Student-J (neither is asked for its trained register), so the arm measures the
decision channel only. WHICH probes are separate calls. Arm 3b first compresses (value-dense,
40 words, per the row-27 guard fix), then runs the original-policy guard probe and the
counterfactual probe against the artifact; the >= 0.70 both-sides guard is checked at scoring
time BEFORE any student cf call is interpreted (and the guard probe precedes cf in call order).

--model is the vLLM served-model name (e.g. the base id or a LoRA adapter name registered with
--lora-modules). VLLM_BASE env overrides http://127.0.0.1:8000/v1.
"""
import argparse
import json
import os
import re
import sys
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
VLLM_BASE = os.environ.get("VLLM_BASE", "http://127.0.0.1:8000/v1")
CAP = int(os.environ.get("CALL_CAP", "250000"))
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)

# Probe wording = experiments/lib/dissociation.py variant 0, verbatim.
COMPRESS_SYS = ("You are a context compaction engine for an operations assistant. Compress the "
                "following record to at most {wl} words. A future analyst will need to answer "
                "questions about it, but you do not know which questions. Output only the "
                "compressed notes.")
COMPRESS_VD_SYS = ("You are a context compaction engine for an operations assistant. Compress "
                   "the following record to at most {wl} words. A future analyst will need to "
                   "answer questions about it, but you do not know which questions. Preserve "
                   "concrete readings: parameter names with their numeric values and units are "
                   "the highest-value content. Output only the compressed notes.")
DECISION = (" Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED "
            "or ANSWER: DENIED.")
WHICH = (" If the decision is DENIED, name the single parameter whose reading caused it. Reply "
         "exactly: PARAMETER: <name> or PARAMETER: NONE.")
ABSTAIN = (" If the notes do not contain enough information to determine this, reply exactly: "
           "PARAMETER: INSUFFICIENT_EVIDENCE.")
NONOTES = (" Based only on the policy and general plausibility (no case notes), guess: "
           "ANSWER: APPROVED or ANSWER: DENIED.")
# Teacher trace requests — MUST stay byte-identical to trace_builder.py V_REQ / J_REQ.
TEACHER_V = (" Was the decision APPROVED or DENIED per policy? "
             "Reply exactly: ANSWER: APPROVED or ANSWER: DENIED.")
TEACHER_J = (" State the decision and its justification in the fusion register: one clause that "
             "names the verdict together with the deciding reading(s) and threshold(s) — never a "
             "verdict without its deciding value in the same clause. Then on a new line reply "
             "exactly: PARAMETER: <failing parameter name> if DENIED, or PARAMETER: NONE if "
             "APPROVED. If a needed reading is absent, say [MISSING DATA] and name what is missing.")
# Revision 1 (revision_protocol.md, frozen before its probe): verdict-after-evidence ordering.
# MUST stay byte-identical to trace_builder.py J_REQ_R1.
TEACHER_J_R1 = (" For each policy parameter, quote its observed reading from the case file next "
                "to its policy threshold and state whether it passes or fails — never assert any "
                "conclusion without the deciding reading in the same clause. If a needed reading "
                "is absent from the file, write [MISSING DATA] and name what is missing. Then end "
                "with exactly two lines:\nDECISION: APPROVED or DECISION: DENIED\n"
                "PARAMETER: <the single failing parameter name> or PARAMETER: NONE")

MAXTOK = dict(compress=256, compress_vd=256, decision=64, which=192, which_abstain=192,
              nonotes=48, teacher_v=32, teacher_j=256, cap_answer=512,
              guard_decision=64, cf_decision=64, cf_which=192)


def load_items(name):
    return [json.loads(l) for l in open(os.path.join(HERE, name))]


def fulldoc_prompt(item, req, policy_key="policy_text"):
    return item[policy_key] + "\n\nCase file:\n" + item["document"] + "\n\n" + req.strip()


def notes_prompt(item, summary, req, policy_key="policy_text"):
    return item[policy_key] + "\n\nCompressed case notes:\n" + summary + "\n\n" + req.strip()


class Client:
    def __init__(self, model, raw_path):
        self.model, self.raw_path = model, raw_path
        self.lock = threading.Lock()
        self.cache = {}
        if os.path.exists(raw_path):
            for line in open(raw_path):
                r = json.loads(line)
                self.cache[(r["model"], r["item"], r["call"], r["variant"])] = r
        self.n0 = len(self.cache)

    def chat(self, iid, call, messages, system=None):
        key = (self.model, iid, call, 0)
        with self.lock:
            if key in self.cache:
                return self.cache[key]["text"]
            if len(self.cache) - self.n0 + 1 > CAP:
                print(f"HARD CAP {CAP} reached", flush=True)
                os._exit(2)
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        body = json.dumps(dict(model=self.model, messages=msgs, temperature=0,
                               max_tokens=MAXTOK.get(call, 128), seed=0,
                               chat_template_kwargs={"enable_thinking": False})).encode()
        req = urllib.request.Request(VLLM_BASE + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            out = json.loads(resp.read())
        text = THINK_RE.sub("", out["choices"][0]["message"]["content"] or "").strip()
        usage = out.get("usage", {})
        rec = dict(model=self.model, item=iid, call=call, variant=0, text=text, usage=usage)
        with self.lock:
            if key not in self.cache:  # concurrent duplicate: first writer wins
                with open(self.raw_path, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                self.cache[key] = rec
        return self.cache[key]["text"]


def run_items(c, items, per_item, workers, label):
    done = [0]
    lock = threading.Lock()

    def work(it):
        per_item(c, it)
        with lock:
            done[0] += 1
            if done[0] % 100 == 0:
                print(f"  {label} {done[0]}/{len(items)}", flush=True)

    if workers <= 1:
        for it in items:
            work(it)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(work, items))


def item_traces(c, it):
    c.chat(it["id"], "teacher_v", [dict(role="user", content=fulldoc_prompt(it, TEACHER_V))])
    c.chat(it["id"], "teacher_j", [dict(role="user", content=fulldoc_prompt(it, TEACHER_J))])


def item_traces_r1(c, it):
    c.chat(it["id"], "teacher_v", [dict(role="user", content=fulldoc_prompt(it, TEACHER_V))])
    c.chat(it["id"], "teacher_j", [dict(role="user", content=fulldoc_prompt(it, TEACHER_J_R1))])


def item_probe_j(c, it):
    c.chat(it["id"], "teacher_j", [dict(role="user", content=fulldoc_prompt(it, TEACHER_J_R1))])


def item_decision(c, it):
    c.chat(it["id"], "decision", [dict(role="user", content=fulldoc_prompt(it, DECISION))])


def item_capability(c, it):
    c.chat(it["id"], "cap_answer", [dict(role="user", content=it["prompt"])])


def item_delta(c, it, budget=15):
    iid = it["id"]
    summary = c.chat(iid, "compress", [dict(role="user", content=it["document"])],
                     system=COMPRESS_SYS.format(wl=budget))
    c.chat(iid, "decision", [dict(role="user", content=notes_prompt(it, summary, DECISION))])
    c.chat(iid, "which", [dict(role="user", content=notes_prompt(it, summary, WHICH))])
    c.chat(iid, "which_abstain",
           [dict(role="user", content=notes_prompt(it, summary, WHICH + ABSTAIN))])
    c.chat(iid, "nonotes", [dict(role="user", content=it["policy_text"] + "\n\n" + NONOTES)])


def item_arm3a(c, it):
    c.chat(it["id"], "cf_decision",
           [dict(role="user", content=fulldoc_prompt(it, DECISION, "cf_policy_text"))])


def item_arm3b(c, it, budget=40):
    iid = it["id"]
    summary = c.chat(iid, "compress_vd", [dict(role="user", content=it["document"])],
                     system=COMPRESS_VD_SYS.format(wl=budget))
    c.chat(iid, "guard_decision",
           [dict(role="user", content=notes_prompt(it, summary, DECISION))])
    c.chat(iid, "cf_decision",
           [dict(role="user", content=notes_prompt(it, summary, DECISION, "cf_policy_text"))])
    c.chat(iid, "cf_which",
           [dict(role="user", content=notes_prompt(it, summary, WHICH + ABSTAIN,
                                                   "cf_policy_text"))])


BATTERIES = dict(
    traces=("train_pool.jsonl", item_traces, "teacher_raw.jsonl"),
    # prompt-revision machinery (revision_protocol.md): fresh raw files across a prompt change —
    # the idempotent cache must never serve an old-prompt response for a new-prompt call.
    probe_j=("probe_slice.jsonl", item_probe_j, "probe_j_raw.jsonl"),
    traces_r1=("train_pool_r1.jsonl", item_traces_r1, "teacher_raw_r1.jsonl"),
    parity=("parity_gauge.jsonl", item_decision, "responses_raw.jsonl"),
    dev=("dev_slice.jsonl", item_decision, "responses_raw.jsonl"),
    capability=("capability_items.jsonl", item_capability, "responses_raw.jsonl"),
    delta=("delta_battery.jsonl", item_delta, "responses_raw.jsonl"),
    arm3a=("arm3.jsonl", item_arm3a, "responses_raw.jsonl"),
    arm3b=("arm3.jsonl", item_arm3b, "responses_raw.jsonl"),
    realdoc=(os.path.join(REPO, "experiments", "realdoc", "2026-07-08", "items.jsonl"),
             item_delta, "responses_raw.jsonl"),
)


def smoke():
    print("=" * 78, "\nSMOKE — first 3 items per battery, prompts only (no calls)\n", "=" * 78)
    pool = load_items("train_pool.jsonl")[:3]
    for it in pool:
        print(f"\n--- traces/{it['id']} teacher_v ---\n{fulldoc_prompt(it, TEACHER_V)[:900]}")
        print(f"\n--- traces/{it['id']} teacher_j (request tail) ---\n...{TEACHER_J}")
    for mode in ("parity", "delta", "arm3a", "arm3b", "realdoc"):
        path = BATTERIES[mode][0]
        items = [json.loads(l) for l in open(path if os.path.isabs(path)
                                             else os.path.join(HERE, path))][:3]
        it = items[0]
        if mode == "parity":
            print(f"\n--- parity/{it['id']} ---\n{fulldoc_prompt(it, DECISION)[:700]}")
        elif mode in ("delta", "realdoc"):
            print(f"\n--- {mode}/{it['id']} compress sys ---\n{COMPRESS_SYS.format(wl=15)}")
            print(f"--- {mode}/{it['id']} probe tail ---\n{DECISION}\n{WHICH}\n{WHICH + ABSTAIN}")
        elif mode == "arm3a":
            print(f"\n--- arm3a/{it['id']} (FULL DOC + CF POLICY) ---\n"
                  f"{fulldoc_prompt(it, DECISION, 'cf_policy_text')[:700]}")
        elif mode == "arm3b":
            print(f"\n--- arm3b/{it['id']} compress sys ---\n{COMPRESS_VD_SYS.format(wl=40)}")
            print(f"--- arm3b cf tail ---\n{DECISION}  [guard uses policy_text; cf uses "
                  f"cf_policy_text]\ncf policy: {it['cf_policy_text'][:250]}")
    print("\nsmoke: prompt construction OK on all batteries")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=list(BATTERIES) + ["smoke"])
    ap.add_argument("--model", help="vLLM served-model name")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent requests (vLLM batches them; cache stays idempotent)")
    a = ap.parse_args()
    if a.mode == "smoke":
        smoke()
        return
    if not a.model:
        sys.exit("--model required for battery modes")
    path, per_item, raw = BATTERIES[a.mode]
    items = [json.loads(l) for l in open(path if os.path.isabs(path)
                                         else os.path.join(HERE, path))]
    if a.limit:
        items = items[:a.limit]
    c = Client(a.model, os.path.join(HERE, raw))
    run_items(c, items, per_item, a.workers, a.mode)
    print(f"{a.mode} done: {len(c.cache)} records in {raw}")


if __name__ == "__main__":
    main()
