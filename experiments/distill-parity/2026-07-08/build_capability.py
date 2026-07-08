#!/usr/bin/env python3
"""Build the external capability-parity slice (pod-side): 250 GSM8K + 250 MMLU, seeded.

Runs on the pod (needs `datasets`). Writes capability_items.jsonl with
{id, kind, prompt, gold}. Prompts request a bare final ANSWER: line so scoring is a string
match; thinking stays off at request time (runner contract). Deterministic in SEED.
"""
import json
import os
import random

from datasets import load_dataset

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 812980
N_EACH = 250

GSM_REQ = ("\n\nSolve the problem. End your reply with exactly one line: "
           "ANSWER: <final integer or decimal>.")
MMLU_REQ = ("\n\nPick the single best option. End your reply with exactly one line: "
            "ANSWER: <A, B, C, or D>.")


def main():
    rng = random.Random(SEED)
    out = []
    gsm = load_dataset("openai/gsm8k", "main", split="test")
    for i in sorted(rng.sample(range(len(gsm)), N_EACH)):
        row = gsm[i]
        gold = row["answer"].split("####")[-1].strip().replace(",", "")
        out.append(dict(id=f"gsm8k-{i:04d}", kind="gsm8k",
                        prompt=row["question"].strip() + GSM_REQ, gold=gold))
    mmlu = load_dataset("cais/mmlu", "all", split="test")
    for i in sorted(rng.sample(range(len(mmlu)), N_EACH)):
        row = mmlu[i]
        choices = "\n".join(f"{l}. {c}" for l, c in zip("ABCD", row["choices"]))
        out.append(dict(id=f"mmlu-{i:05d}", kind="mmlu",
                        prompt=row["question"].strip() + "\n\n" + choices + MMLU_REQ,
                        gold="ABCD"[row["answer"]]))
    with open(os.path.join(HERE, "capability_items.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(out)} capability items (seed {SEED})")


if __name__ == "__main__":
    main()
