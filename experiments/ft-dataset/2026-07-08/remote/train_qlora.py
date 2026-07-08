#!/usr/bin/env python3
"""B4 calibrated-reader QLoRA — remote GPU trainer (RunPod, single 24GB+ card).

Usage on the pod (from the directory containing this file + train.jsonl + valid.jsonl):
    pip install -q "transformers==4.53.3" "trl==0.19.1" "peft==0.16.0" \
                   "bitsandbytes==0.46.0" "datasets==3.6.0" accelerate
    python3 train_qlora.py

Writes the LoRA adapter to ./adapter/ — copy that single directory back to the repo at
experiments/ft-dataset/2026-07-08/remote/adapter/. Config mirrors training_plan.md Option B
(rank 16, alpha 32, dropout 0.05, 4-bit nf4, 3 epochs, cosine, lr 2e-4) and the frozen
prereg_b4_eval.md thresholds apply to the eval, not the training.
"""
import json

import torch
from datasets import load_dataset
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

BASE = "Qwen/Qwen3-4B-Instruct-2507"

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

data = load_dataset(
    "json", data_files={"train": "train.jsonl", "eval": "valid.jsonl"}
)

trainer = SFTTrainer(
    model=model,
    processing_class=tok,
    train_dataset=data["train"],
    eval_dataset=data["eval"],
    peft_config=LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    ),
    args=SFTConfig(
        output_dir="adapter",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        max_length=1024,
        packing=True,
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        bf16=True,
        gradient_checkpointing=True,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        report_to=[],
        seed=7,
    ),
)
trainer.train()
trainer.save_model("adapter")
metrics = trainer.evaluate()
json.dump(metrics, open("adapter/final_eval_metrics.json", "w"), indent=1)
print("DONE — adapter/ ready to copy back:", metrics)
