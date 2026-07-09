#!/usr/bin/env python3
"""Forced-CoT probe runner (pod-side, vLLM OpenAI endpoint). Stdlib only.

    python3 runner_fc.py smoke --model base            # 3 items/arm, spot-read
    python3 runner_fc.py run --model sv --workers 24   # all arms for one served model
Contract: temp 0, enable_thinking false, <think> stripped, idempotent cache keyed
(model,item,call), hard cap. Prereg: prereg_forced_cot.md (frozen before spend).
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
VLLM_BASE = os.environ.get("VLLM_BASE", "http://127.0.0.1:8000/v1")
RAW = os.path.join(HERE, "responses_raw.jsonl")
CAP = 20000
THINK_RE = re.compile(r"<think>.*?</think>\s*", re.S)
SERVED = dict(sv="sv", sj="sj", base="Qwen/Qwen3-1.7B")

DECISION = (" Was the decision APPROVED or DENIED per policy? Reply exactly: ANSWER: APPROVED "
            "or ANSWER: DENIED.")
DECISION_COT = (" Check each policy parameter against the case file step by step, quoting each "
                "reading you can find, then reply on the final line exactly: ANSWER: APPROVED "
                "or ANSWER: DENIED.")
ABSTAIN = (" If the file does not contain enough information to determine this, reply exactly: "
           "ANSWER: INSUFFICIENT_EVIDENCE.")
CAP_COT = ("\n\nWork through the problem step by step, showing your reasoning, then end with "
           "exactly one line: ANSWER: <final answer>.")
MAXTOK = dict(cap_cot=900, abl_bare=512, abl_cot=900, abl_abstain=512)


def doc_prompt(it, req):
    return it["policy_text"] + "\n\nCase file:\n" + it["document_ablated"] + "\n\n" + req.strip()


class Client:
    def __init__(self, model):
        self.model = model
        self.lock = threading.Lock()
        self.cache = {}
        if os.path.exists(RAW):
            for line in open(RAW):
                r = json.loads(line)
                self.cache[(r["model"], r["item"], r["call"])] = r
        self.n0 = len(self.cache)

    def chat(self, iid, call, content):
        key = (self.model, iid, call)
        with self.lock:
            if key in self.cache:
                return
            if len(self.cache) - self.n0 + 1 > CAP:
                os._exit(2)
        body = json.dumps(dict(model=SERVED[self.model], messages=[dict(role="user", content=content)],
                               temperature=0, max_tokens=MAXTOK[call], seed=0,
                               chat_template_kwargs={"enable_thinking": False})).encode()
        req = urllib.request.Request(VLLM_BASE + "/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            out = json.loads(resp.read())
        text = THINK_RE.sub("", out["choices"][0]["message"]["content"] or "").strip()
        rec = dict(model=self.model, item=iid, call=call, text=text,
                   usage=out.get("usage", {}))
        with self.lock:
            if key not in self.cache:
                with open(RAW, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                self.cache[key] = rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["smoke", "run"])
    ap.add_argument("--model", required=True, choices=list(SERVED))
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    cap_items = [json.loads(l) for l in open(os.path.join(HERE, "capability_items.jsonl"))]
    abl_items = [json.loads(l) for l in open(os.path.join(HERE, "sections_items.jsonl"))]
    if a.mode == "smoke":
        cap_items, abl_items = cap_items[:3], abl_items[:3]
    c = Client(a.model)
    jobs = ([("cap_cot", it["id"], it["prompt"].rsplit("\n\n", 1)[0] + CAP_COT) for it in cap_items]
            + [(call, it["id"], doc_prompt(it, req)) for it in abl_items
               for call, req in (("abl_bare", DECISION), ("abl_cot", DECISION_COT),
                                 ("abl_abstain", DECISION + ABSTAIN))])
    done = [0]
    lock = threading.Lock()

    def work(j):
        call, iid, content = j
        c.chat(iid, call, content)
        with lock:
            done[0] += 1
            if done[0] % 100 == 0:
                print(f"  {a.model} {done[0]}/{len(jobs)}", flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        list(ex.map(work, jobs))
    print(f"{a.model} done: {len(c.cache)} records")
    if a.mode == "smoke":
        for k, r in list(c.cache.items()):
            if k[0] == a.model:
                print("====", k[2], "tok:", r["usage"].get("completion_tokens"))
                print(r["text"][:300], "\n")


if __name__ == "__main__":
    main()
