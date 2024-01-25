#!/bin/sh

python3 -m venv /tmp/eval_env

chmod +x /tmp/eval_env/bin/activate

. /tmp/eval_env/bin/activate

git clone https://github.com/EleutherAI/lm-evaluation-harness /tmp/lm-evaluation-harness

cd /tmp/lm-evaluation-harness

pip install -e .

# MODEL="EleutherAI/gpt-neo-125M"
MODEL="/data/models/src"
# PEFT="/data/adapters/toe/base"

lm_eval --model hf \
    --model_args pretrained=${MODEL},cache_dir=/data/models,trust_remote_code=True \
    # --model_args pretrained=${MODEL},peft=${PEFT},cache_dir=/data/models,trust_remote_code=True \
    --tasks arc_easy,arc_challenge,hellaswag,openbookqa,piqa \
    --device cuda:1 \
    --batch_size auto
