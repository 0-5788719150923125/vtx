import json
import logging
import math
import os
import random
import re
import shutil
import subprocess
import time

import torch

from common import (
    colors,
    config,
    focus,
    get_directory_size,
    hash_directory,
    list_full_paths,
    nist_beacon,
)

model_config = config[focus]
p = model_config["training"]

devices = None
device_map = p.get("device_map", "auto")
if focus in ["frame"]:
    devices = device_map.split(":")[1]
    os.environ["CUDA_VISIBLE_DEVICES"] = str(devices)

from lightning.pytorch import loggers
from moduleformer import (
    ModuleFormerConfig,
    ModuleFormerForCausalLM,
    ModuleFormerForSequenceClassification,
)
from peft import (
    AdaLoraConfig,
    IA3Config,
    LoHaConfig,
    LoKrConfig,
    LoraConfig,
    PeftConfig,
    PeftModel,
    PrefixTuningConfig,
    PromptTuningConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from pypdf import PdfReader
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from aigen.aigen import aigen
from aigen.aigen.datasets import TokenDataset, merge_datasets

AutoConfig.register("moduleformer", ModuleFormerConfig)
AutoModelForCausalLM.register(ModuleFormerConfig, ModuleFormerForCausalLM)
AutoModelForSequenceClassification.register(
    ModuleFormerConfig, ModuleFormerForSequenceClassification
)


def main():
    print("(" + colors.GREEN + "focus" + colors.WHITE + ")")
    time.sleep(2)
    print(f"({colors.RED}ed{colors.WHITE}) on the ({colors.BLUE}{focus}{colors.WHITE})")
    time.sleep(3)

    base_model = model_config["model"]
    model_folder = "/data/models/" + focus
    launch_model = None
    fresh_logs = False
    resume = p.get("resume", False)
    use_petals = model_config.get("petals", False)
    adapter = p.get("name", "base")

    regen = p.get("regen", False)
    if regen:
        shutil.rmtree(f"/data/datasets/{focus}", ignore_errors=True)

    # Resume training on an existing model, or start with a fresh base model
    if resume == True:
        if not os.path.exists(
            "/data/models/" + focus + "/pytorch_model.bin"
        ) and not os.path.exists("/data/models/" + focus + "/model.safetensors"):
            launch_model = base_model
            model_folder = None
    else:
        fresh_logs = True
        launch_model = base_model
        model_folder = None
        shutil.rmtree(f"/data/models/{focus}", ignore_errors=True)
        shutil.rmtree(f"/data/embeddings/{focus}", ignore_errors=True)

    tuning_mode = None
    pretrain_config = None
    peft_config = None
    pre_seq_len = 0

    output_dir = f"/data/models/{focus}"
    train_type = p.get("type", "standard")

    if train_type == "pretrain" and not resume:
        pretrain_config = AutoConfig.from_pretrained(launch_model)
        print(f"{colors.RED}original pretrain config:{colors.WHITE}")
        print(pretrain_config)
        setattr(pretrain_config, "_name_or_path", focus)
        for k, v in p.get("overrides").items():
            setattr(pretrain_config, k, v)
        print(f"{colors.GREEN}modified pretrain config:{colors.WHITE}")
        print(pretrain_config)

    if train_type not in ["standard", "pretrain"] and not use_petals:
        output_dir = f"/data/adapters/{focus}/{adapter}"

    tokenizer = AutoTokenizer.from_pretrained(
        base_model,
        cache_dir="/data/models",
        padding="max_length",
        padding_side=p.get("padding_side", "left"),
        use_fast=True,
        return_overflowing_tokens=True,
        truncation=True,
        trust_remote_code=True,
    )

    print(tokenizer)

    static_data = []
    if len(p["datasets"].get("static", [])) > 0:
        static_data.append(build_static_datasets(p, tokenizer))

    gradient_checkpointing = p.get("gradient_checkpointing", True)

    # Instantiate the model object
    prototype = aigen(
        model=launch_model,
        model_folder=model_folder,
        tokenizer=tokenizer,
        config=pretrain_config,
        petals=use_petals,
        cache_dir="/data/models",
        embeddings_dir="/data/embeddings/" + focus,
        tuning_mode=tuning_mode,
        pre_seq_len=pre_seq_len,
        precision=model_config.get("precision", 32),
        gradient_checkpointing=gradient_checkpointing,
        device_map=device_map,
    )

    prototype.attach_adapter(output_dir, p)

    if hasattr(prototype.model, "training"):
        prototype.model.training = True

    print(prototype.model)

    if hasattr(prototype.model, "print_trainable_parameters"):
        prototype.model.print_trainable_parameters()

    gradient_accumulation_steps = p.get("gradient_accumulation_steps", 1)
    batch_size = p.get("batch_size", 1)

    # Erase old logs
    log_path = "/data/logs/" + focus
    if fresh_logs == True:
        shutil.rmtree(log_path, ignore_errors=True)

    os.makedirs(f"{log_path}/{adapter}", exist_ok=True)

    logger = loggers.TensorBoardLogger(log_path, name=adapter, default_hp_metric=True)

    block_size = p.get("block_size", 2048)
    val_interval = p.get("val_interval", 1000)

    if len(static_data) > 0:
        dataset_size = get_directory_size(f"/data/datasets/{focus}")

        print(
            f"Training data:\n{colors.GREEN}{dataset_size:.2f}{colors.WHITE} GB, {colors.GREEN}{len(static_data[0])}{colors.WHITE} batches, {colors.GREEN}{len(static_data[0]) * block_size}{colors.WHITE} tokens"
        )

        if val_interval > len(static_data[0]):
            val_interval = math.floor(len(static_data[0]) / 2)

    streaming_data = []
    for dataset in p["datasets"].get("streaming", []):
        streaming_data.append(config["collections"]["streaming"][dataset.lower()])

    # Train the model
    prototype.train(
        static_data=static_data,
        streaming_data=streaming_data,
        generation_config=config["transformers"]["generation"][
            model_config.get("generation_profile", "training")
        ],
        strategy=p.get("strategy"),
        initial_peers=p.get("initial_piers", []),
        devices=devices,
        petals=use_petals,
        seed=nist_beacon()[1],
        output_dir=output_dir,
        loggers=[logger],
        batch_size=batch_size,
        target_batch_size=p.get("target_batch_size", 8192),
        num_steps=p.get("num_steps", 33333),
        generate_every=p.get("generate_every", 500),
        save_every=p.get("save_every", 1000),
        optimizer=p.get("optimizer", "AdamW"),
        loss_function=p.get("loss_function", "default"),
        learning_rate=float(p.get("learning_rate", 0.005)),
        lookahead=p.get("lookahead", 0),
        momentum=float(p.get("momentum", 0)),
        swa_learning_rate=p.get("swa_learning_rate", None),
        weight_decay=float(p.get("weight_decay", 0)),
        warmup_steps=p.get("warmup_steps", 0),
        gradient_clip_val=p.get("gradient_clip_val", 0.5),
        update_period=p.get("update_period", 10),
        gradient_accumulation_steps=gradient_accumulation_steps,
        scheduler=p.get("scheduler", "linear"),
        num_cycles=p.get("num_cycles", None),
        prune=p.get("prune", 0.0),
        block_size=block_size,
        val_split=p.get("val_split", 0.0),
        val_interval=val_interval,
        finetune=p.get("finetune", False),
        checkpoint=p.get("checkpoint", False),
    )


# Join every file located in a particular directory
def create_dataset(
    path="/lab",
    tokenizer=None,
    block_size: int = 1024,
    stride: int = 0,
    samples: float = 1.0,
    line_by_line=False,
):
    prefixes = [
        ".git",
        "/lab/reaper/logseq",
        "/lab/reaper/assets",
        "/lab/reaper/public",
        "/lab/aigen/aigen/static",
        "/lab/opencog/learn/learn-lang-diary",
        "/src/__pycache__",
        "/src/lab/__pycache__",
    ]

    suffixes = [
        "7z",
        "bib",
        "bin",
        "eot",
        "eps",
        "epub",
        "docx",
        "gif",
        "ico",
        ".in",
        "jpg",
        "jpeg",
        "mp3",
        "mp4",
        "odt",
        ".out",
        # "pdf",
        "png",
        "pt",
        "pyc",
        "related.tex",
        "resources/content.xml",
        "resources/meta.xml",
        "sqlite",
        "synctex",
        "toascii",
        "ttf",
        "woff",
        "woff2",
        "xlsx",
        "zip",
    ]

    files = list_full_paths(path)
    random.shuffle(files)

    files = [item for item in files if random.random() < samples]

    intermediate_path = "/tmp/intermediate.txt"

    datasets = {}
    for file in files:
        try:
            # Skip file paths and extensions that we can't process
            skip = False
            for suffix in suffixes:
                if file.lower().endswith(suffix):
                    skip = True
                    continue
            for prefix in prefixes:
                if file.startswith(prefix):
                    skip = True
                    continue
            if skip == True:
                print(f"skipping: {colors.RED}{file}{colors.WHITE}")
                continue

            if line_by_line == True:
                with open(file, "r") as content:
                    with open("/tmp/lines.txt", "a") as lines:
                        lines.write(content.read())
                datasets[file] = TokenDataset(
                    "/tmp/lines.txt",
                    batch_size=100000,
                    block_size=block_size,
                    line_by_line=line_by_line,
                    tokenizer=tokenizer,
                    stride=stride,
                    bos_token=tokenizer.bos_token or "<|endoftext|>",
                    eos_token=tokenizer.eos_token or "<|endoftext|>",
                    unk_token=tokenizer.unk_token or "<|endoftext|>",
                    pad_token=tokenizer.pad_token or "<|endoftext|>",
                )
                os.remove("/tmp/lines.txt")
            else:
                with open(file, "r") as content:
                    with open(intermediate_path, "a") as intermediate:
                        string = ""
                        if file.lower().endswith("pdf"):
                            reader = PdfReader(file)
                            for i, page in enumerate(reader.pages):
                                page = reader.pages[i].extract_text()
                                string += page + "\n"
                        else:
                            string = content.read()
                        intermediate.write(string + f"{tokenizer.eos_token}")

        except Exception as e:
            print(f"failed: {colors.RED}{file}{colors.WHITE}")
            logging.error(e)

    print(f"tokenizing: {colors.BLUE}{path}{colors.WHITE}")

    if line_by_line == True:
        collection = []
        for dataset in datasets:
            collection.append(datasets[dataset])
        if len(collection) == 1:
            dataset = collection[0]
        else:
            dataset = merge_datasets(collection, equalize=False)
    else:
        dataset = TokenDataset(
            intermediate_path,
            tokenizer=tokenizer,
            batch_size=100000,
            block_size=block_size,
            stride=stride,
            bos_token=tokenizer.bos_token or "<|endoftext|>",
            eos_token=tokenizer.eos_token or "<|endoftext|>",
            unk_token=tokenizer.unk_token or "<|endoftext|>",
            pad_token=tokenizer.pad_token or "<|endoftext|>",
        )

    # Cleanup temp files used for tokenized dataset creation
    if os.path.exists("/tmp/intermediate.txt"):
        os.remove("/tmp/intermediate.txt")

    return dataset


# Create a tokenized dataset from every directory specified in config file
def build_static_datasets(c, tokenizer):
    datasets = {}
    block_size = c.get("block_size")
    stride = c.get("stride", 0)
    for collection in c["datasets"]["static"]:
        for dataset in config["collections"]["static"][collection]:
            if dataset not in datasets:
                ds_config = config["collections"]["static"][collection][dataset] or {}

                duplicate = ds_config.get("duplicate", 0)

                cache_path = f"{focus}/{str(block_size)}/{dataset}"
                hashed = hash_directory("/" + dataset)
                while duplicate >= 0:
                    new_path = f"{cache_path}/{str(duplicate)}"
                    print(f"loading: {colors.BLUE}{new_path}{colors.WHITE}")

                    cached = f"/data/datasets/{new_path}/{hashed}.tar.gz"

                    if os.path.exists(cached):
                        datasets[dataset + str(duplicate)] = TokenDataset(
                            cached,
                            block_size=block_size,
                            from_cache=True,
                        )
                        duplicate -= 1
                        continue

                    shutil.rmtree(f"/data/datasets/{new_path}", ignore_errors=True)

                    os.makedirs(f"/data/datasets/{new_path}", exist_ok=True)

                    ds = create_dataset(
                        path="/" + dataset,
                        tokenizer=tokenizer,
                        block_size=block_size,
                        stride=ds_config.get("stride", stride),
                        samples=ds_config.get("samples", 1.0),
                        line_by_line=ds_config.get("line_by_line", False),
                    )

                    ds.save(cache_destination=cached)

                    datasets[dataset + str(duplicate)] = ds

                    duplicate -= 1

            else:
                print(
                    colors.GREEN
                    + dataset
                    + colors.WHITE
                    + " is already loaded into memory"
                )

    # Merge all tokenized datasets into a single dataset for training
    collected = []
    for collection in c["datasets"]["static"]:
        for dataset in config["collections"]["static"][collection]:
            duplicate = 0
            while dataset + str(duplicate) in datasets:
                collected.append(datasets[dataset + str(duplicate)])
                duplicate = duplicate + 1
    if len(collected) > 1:
        return merge_datasets(collected, equalize=c.get("equalize_datasets", False))
    else:
        return collected[0]


if __name__ == "__main__":
    main()
