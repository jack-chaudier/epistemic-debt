# B4 remote QLoRA — RunPod runbook

One 24GB+ GPU (RTX 4090 / A5000 / A100), PyTorch template, ~1–2 GPU-hours, est. $2–5 spot.
Training data is synthetic-experiment derived (no secrets — verified by the repo key-scan test),
so uploading it to a rented pod is fine. The frozen eval prereg is `../prereg_b4_eval.md`.

## Steps

1. **You (account holder):** create the pod on runpod.io — template "RunPod PyTorch", GPU
   RTX 4090, container disk ≥ 30 GB. Grab the SSH connection string from the pod's Connect tab.
2. **Upload** (from repo root; substitute the pod's ssh string/port):
   ```bash
   scp -P <port> experiments/ft-dataset/2026-07-08/mlx/data/train.jsonl \
       experiments/ft-dataset/2026-07-08/mlx/data/valid.jsonl \
       experiments/ft-dataset/2026-07-08/remote/train_qlora.py root@<pod-ip>:/workspace/
   ```
3. **Train** (on the pod):
   ```bash
   cd /workspace
   pip install -q "transformers==4.53.3" "trl==0.19.1" "peft==0.16.0" \
                  "bitsandbytes==0.46.0" "datasets==3.6.0" accelerate
   nohup python3 train_qlora.py > train.log 2>&1 &
   tail -f train.log     # ~3 epochs over 5,021 examples; watch eval_loss per epoch
   ```
4. **Retrieve** (from repo root) and **stop the pod** (billing stops when you do):
   ```bash
   scp -r -P <port> root@<pod-ip>:/workspace/adapter \
       experiments/ft-dataset/2026-07-08/remote/adapter
   ```
5. Back on the Mac, the preregistered before/after battery runs locally against
   base-vs-adapter (mlx or transformers inference at low intensity — the lead session drives it).

The `meta` key was already stripped from train/valid JSONL (messages-only format).
