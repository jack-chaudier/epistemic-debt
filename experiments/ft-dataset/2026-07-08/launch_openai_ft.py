#!/usr/bin/env python3
"""Launch an OpenAI supervised fine-tune of gpt-4.1-mini on the calibrated-reader dataset.

DO NOT RUN without lead authorization — this spends money (training-token billing). It is
written so the only thing standing between here and a job is one authorized invocation.

  export OPENAI_API_KEY=...            # from the environment, never written to disk
  python3 launch_openai_ft.py --dry-run     # prints token/cost estimate, uploads nothing
  python3 launch_openai_ft.py --go          # uploads files + creates the fine-tune job

The dataset lines carry a `meta` block for our bookkeeping; OpenAI wants pure {"messages":[...]}.
This script projects each line to messages-only into *.openai.jsonl before upload.

Requires the `openai` python package (the only place in this repo that is not stdlib-only; it is
never imported by the builder or the test). Pricing constants are pinned below with a date and
MUST be re-verified against https://openai.com/api/pricing before a real launch.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TRAIN = os.path.join(HERE, "dataset_train.jsonl")
EVAL = os.path.join(HERE, "dataset_eval.jsonl")

BASE_MODEL = "gpt-4.1-mini-2025-04-14"
N_EPOCHS = 3
# pinned 2026-07-08 — VERIFY before spending. gpt-4.1-mini fine-tuning, USD per 1M tokens.
FT_TRAIN_USD_PER_M = 5.00     # training-token price
FT_INPUT_USD_PER_M = 0.80     # fine-tuned inference input
FT_OUTPUT_USD_PER_M = 3.20    # fine-tuned inference output


def project(src, dst):
    """Strip meta -> messages-only jsonl. Returns (n, approx_tokens)."""
    n, chars = 0, 0
    with open(src) as f, open(dst, "w") as g:
        for line in f:
            r = json.loads(line)
            rec = {"messages": r["messages"]}
            g.write(json.dumps(rec) + "\n")
            n += 1
            chars += sum(len(m["content"]) for m in r["messages"])
    return n, chars // 4          # ~4 chars/token heuristic (upper-bounded by real tokenizer)


def estimate():
    tr_dst = os.path.join(HERE, "dataset_train.openai.jsonl")
    ev_dst = os.path.join(HERE, "dataset_eval.openai.jsonl")
    n_tr, tok_tr = project(TRAIN, tr_dst)
    n_ev, tok_ev = project(EVAL, ev_dst)
    train_tokens = tok_tr * N_EPOCHS
    cost = train_tokens / 1e6 * FT_TRAIN_USD_PER_M
    print("base model      :", BASE_MODEL)
    print("train examples  :", n_tr, "(~%d tok/epoch)" % tok_tr)
    print("eval examples   :", n_ev, "(~%d tok)" % tok_ev)
    print("epochs          :", N_EPOCHS)
    print("train tokens    : ~%d (%d epochs)" % (train_tokens, N_EPOCHS))
    print("est. TRAIN cost : ~$%.2f  (@ $%.2f/1M, VERIFY pricing)" % (cost, FT_TRAIN_USD_PER_M))
    print("fine-tuned inference: $%.2f in / $%.2f out per 1M" % (FT_INPUT_USD_PER_M, FT_OUTPUT_USD_PER_M))
    print("projected files :", tr_dst, ev_dst)
    return tr_dst, ev_dst


def launch():
    tr_dst, ev_dst = estimate()
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY not set")
    from openai import OpenAI               # imported only on a real launch
    client = OpenAI()
    tr_file = client.files.create(file=open(tr_dst, "rb"), purpose="fine-tune")
    ev_file = client.files.create(file=open(ev_dst, "rb"), purpose="fine-tune")
    print("uploaded train file:", tr_file.id, "| eval file:", ev_file.id)
    job = client.fine_tuning.jobs.create(
        training_file=tr_file.id,
        validation_file=ev_file.id,
        model=BASE_MODEL,
        hyperparameters={"n_epochs": N_EPOCHS},
        suffix="calib-reader-b4")
    print("fine-tune job created:", job.id, "status", job.status)
    print("poll: client.fine_tuning.jobs.retrieve('%s')" % job.id)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--dry-run", action="store_true", help="estimate + project files, upload nothing")
    g.add_argument("--go", action="store_true", help="AUTHORIZED launch: upload + create job")
    a = ap.parse_args()
    if a.dry_run:
        estimate()
    else:
        launch()
