#!/usr/bin/env python3
"""Distill-parity student trainer (pod-side): Qwen3-1.7B QLoRA on one trace set.

    python3 train_distill.py train_V.jsonl student_V
    python3 train_distill.py train_J.jsonl student_J

Config is FROZEN (prereg d24e198): r=16, alpha=32, dropout=0.05, all-linear targets, 3 epochs,
lr 2e-4 cosine, seq 1024, seeded. Identical across conditions — the ONLY difference between the
two invocations is the trace file. Saves a checkpoint per epoch (checkpoint selection happens
on the dev slice per the frozen rule); token-count asymmetry between V and J is disclosed, not
corrected (packing=False so optimizer steps match on example count, not token count).
Deps pinned per the B4 runbook: transformers==4.53.3 trl==0.19.1 peft==0.16.0
bitsandbytes==0.46.0 datasets==3.6.0 accelerate.
"""
import json
import sys

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

BASE = "Qwen/Qwen3-1.7B"
train_file, outdir = sys.argv[1], sys.argv[2]

tok = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(
    BASE,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    ),
    device_map="auto",
)

data = load_dataset("json", data_files={"train": train_file})

trainer = SFTTrainer(
    model=model,
    processing_class=tok,
    train_dataset=data["train"],
    peft_config=LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    ),
    args=SFTConfig(
        output_dir=outdir,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        max_length=1024,
        packing=False,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=20,
        save_strategy="epoch",
        save_total_limit=3,
        report_to=[],
        seed=812,
    ),
)
trainer.train()
trainer.save_model(outdir + "/final")
json.dump(trainer.state.log_history, open(outdir + "/log_history.json", "w"), indent=1)
print(f"DONE — {outdir}: per-epoch checkpoints + final adapter saved")
