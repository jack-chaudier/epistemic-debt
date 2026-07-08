#!/bin/bash
# Pod-side eval driver, phase 1: serve students, run dev battery on all 6 checkpoints,
# then parity+capability on the two named in $SV/$SJ (set by the controller after selection).
# Usage: bash eval_driver.sh dev            — serve + dev battery on all 6 checkpoints
#        SV=sv2 SJ=sj3 bash eval_driver.sh parity   — parity+capability on the selected pair
#        SV=sv2 SJ=sj3 bash eval_driver.sh batteries — delta/arm3a/arm3b/realdoc on the pair
#        bash eval_driver.sh teacher        — swap server to 8B, teacher batteries
set -e
cd /workspace
export HF_HOME=/workspace/hf
VLLM=/workspace/venv-vllm/bin/vllm

serve_students() {
  pkill -f "venv-vllm/bin" 2>/dev/null || true; sleep 5
  CKS=$(ls -d student_V/checkpoint-* | sort -t- -k2 -n | tr '\n' ' ')
  CKJ=$(ls -d student_J/checkpoint-* | sort -t- -k2 -n | tr '\n' ' ')
  set -- $CKS; V1=$1; V2=$2; V3=$3
  set -- $CKJ; J1=$1; J2=$2; J3=$3
  nohup $VLLM serve Qwen/Qwen3-1.7B --dtype bfloat16 --max-model-len 8192 \
    --gpu-memory-utilization 0.90 --enable-lora --max-lora-rank 16 --max-loras 6 \
    --lora-modules sv1=/workspace/$V1 sv2=/workspace/$V2 sv3=/workspace/$V3 \
                   sj1=/workspace/$J1 sj2=/workspace/$J2 sj3=/workspace/$J3 \
    --port 8000 > vllm_students.log 2>&1 &
  until curl -s -m 3 localhost:8000/v1/models 2>/dev/null | grep -q sv3; do sleep 10; done
  echo STUDENTS_SERVED
}

case "$1" in
  dev)
    serve_students
    for M in sv1 sv2 sv3 sj1 sj2 sj3; do
      python3 runner.py dev --model $M --workers 32
    done
    echo DEV_DONE ;;
  parity)
    python3 build_capability.py || echo CAPABILITY_BUILD_FAILED
    for M in $SV $SJ; do
      python3 runner.py parity --model $M --workers 32
      [ -f capability_items.jsonl ] && python3 runner.py capability --model $M --workers 32
    done
    echo PARITY_DONE ;;
  batteries)
    for M in $SV $SJ; do
      python3 runner.py delta   --model $M --workers 32
      python3 runner.py arm3a   --model $M --workers 32
      python3 runner.py arm3b   --model $M --workers 32
      python3 runner.py realdoc --model $M --workers 32
    done
    echo BATTERIES_DONE ;;
  teacher)
    pkill -f "venv-vllm/bin" 2>/dev/null || true; sleep 5
    nohup $VLLM serve Qwen/Qwen3-8B --dtype bfloat16 --max-model-len 8192 \
      --gpu-memory-utilization 0.92 --port 8000 > vllm_teacher2.log 2>&1 &
    until curl -s -m 3 localhost:8000/v1/models 2>/dev/null | grep -q Qwen3-8B; do sleep 10; done
    for MODE in parity delta arm3a arm3b realdoc; do
      python3 runner.py $MODE --model Qwen/Qwen3-8B --workers 32
    done
    [ -f capability_items.jsonl ] && python3 runner.py capability --model Qwen/Qwen3-8B --workers 32
    echo TEACHER_DONE ;;
esac
