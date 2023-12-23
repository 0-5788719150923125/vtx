#!/bin/sh

python3 -m venv /tmp/eval_env

chmod +x /tmp/eval_env/bin/activate

. /tmp/eval_env/bin/activate

git clone https://github.com/EleutherAI/lm-evaluation-harness /tmp/lm-evaluation-harness

cd /tmp/lm-evaluation-harness

pip install -e .

# lm-eval --tasks list

MODEL="EleutherAI/gpt-neo-125M"
PEFT="/data/adapters/toe/base"

lm_eval --model hf \
    --model_args pretrained=${MODEL},peft=${PEFT},cache_dir=/data/models,trust_remote_code=True \
    --tasks arc_easy,arc_challenge,hellaswag,openbookqa,piqa \
    --device cuda:0 \
    --batch_size auto
