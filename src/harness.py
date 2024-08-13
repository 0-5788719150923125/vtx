import logging
import os
import random
import re
import shutil
import sys
import time

import chardet
import torch
from lightning.pytorch import loggers
from pypdf import PdfReader
from tokenizers import Tokenizer
from torch.utils.data import (
    ConcatDataset,
    DataLoader,
    WeightedRandomSampler,
    random_split,
)
from transformers import (
    AutoConfig,
    AutoTokenizer,
    PretrainedConfig,
    PreTrainedTokenizerFast,
)

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "aigen"))
)

try:
    from aigen.aigen import aigen
    from aigen.aigen.datasets import StaticDataset, merge_datasets
    from aigen.aigen.tokenizers import train_tokenizer
    from aigen.aigen.tuners import optimize_hparams
except:
    from aigen import aigen
    from aigen.datasets import StaticDataset, merge_datasets
    from aigen.tokenizers import train_tokenizer
    from aigen.tuners import optimize_hparams

import extensions
from common import (
    colors,
    config,
    focus,
    get_identity,
    hash_directory,
    list_full_paths,
    nist_beacon,
)

model_config = config[focus]
train_config = model_config["training"]

local_rank = int(os.environ.get("LOCAL_RANK", 0))
world_rank = int(os.environ.get("WORLD_RANK", 0))


def print_once(text):
    if local_rank == 0:
        print(text)


def main():
    print_once("(" + colors.GREEN + "focus" + colors.WHITE + ")")
    time.sleep(2)
    print_once(
        f"({colors.RED}ed{colors.WHITE}) on the ({colors.BLUE}{focus}{colors.WHITE})"
    )
    time.sleep(3)

    base_model = model_config.get("model")
    model_folder = "/data/models/" + focus
    launch_model = None
    fresh_logs = train_config.get("refresh_logs", False)
    resume = train_config.get("resume", False)
    use_petals = model_config.get("petals", False)
    adapter = train_config.get("name", "base")

    regen = train_config.get("regen", False)
    if regen:
        shutil.rmtree(f"/data/datasets/{focus}", ignore_errors=True)

    # Resume training on an existing model, or start with a fresh base model
    if resume == True:
        if not os.path.exists(
            "/data/models/" + focus + "/pytorch_model.bin"
        ) or not os.path.exists("/data/models/" + focus + "/model.safetensors"):
            launch_model = base_model
            model_folder = None
    else:
        fresh_logs = True
        launch_model = base_model
        shutil.rmtree(model_folder, ignore_errors=True)
        shutil.rmtree(f"/data/embeddings/{focus}", ignore_errors=True)
        model_folder = None

    tuning_mode = None
    pretrain_config = None
    pre_seq_len = 0

    output_dir = f"/data/models/{focus}"
    train_type = train_config.get("type", "standard")

    tokenizer_model = base_model
    tokenizer_config = dict(
        cache_dir="/data/models",
        padding="max_length",
        padding_side=train_config.get("padding_side", "left"),
        use_fast=True,
        return_overflowing_tokens=True,
        truncation=True,
        trust_remote_code=True,
    )

    if isinstance(train_config.get("tokenizer"), bool):
        tokenizer_model = output_dir
        if not os.path.exists(f"{tokenizer_model}/tokenizer.json"):
            files = list_full_paths(train_config.get("corpus", "/lab/research"))
            existing_files = []
            # Iterate over each file in the list
            for file in files:
                # Check if the file exists
                if os.path.isfile(file):
                    # If the file exists, add it to the existing_files list
                    try:
                        # Try to open the file as UTF-8
                        with open(file, "rb") as f:
                            # Read the contents of the file
                            header = f.read(4)
                            # Detect the encoding of the file
                            result = chardet.detect(header)
                            if result["encoding"] == "utf-8":
                                existing_files.append(file)
                        # If no exception is raised, the file is valid UTF-8
                        existing_files.append(file)
                    except UnicodeDecodeError:
                        continue
            tokenizer = train_tokenizer(
                files=existing_files,
                dropout=0.9,
                vocab_size=train_config["overrides"].get("vocab_size"),
                min_frequency=2,
                save_path=tokenizer_model,
                max_token_length=5,
            )
    elif isinstance(train_config.get("tokenizer"), str):
        tokenizer_model = train_config.get("tokenizer")

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_model, **tokenizer_config)

    if hasattr(tokenizer, "pad_token") and tokenizer.pad_token is None:
        setattr(tokenizer, "pad_token", tokenizer.eos_token)

    print_once(tokenizer)

    if train_type == "pretrain":
        pretrain_config = AutoConfig.for_model(model_type=launch_model)
        print_once(f"{colors.RED}original pretrain config:{colors.WHITE}")
        print_once(pretrain_config)
        setattr(pretrain_config, "_name_or_path", focus)
        setattr(pretrain_config, "bos_token_id", tokenizer.bos_token_id)
        setattr(pretrain_config, "eos_token_id", tokenizer.eos_token_id)
        setattr(pretrain_config, "pad_token_id", tokenizer.pad_token_id)
        setattr(pretrain_config, "unk_token_id", tokenizer.unk_token_id)
        for k, v in train_config.get("overrides").items():
            setattr(pretrain_config, k, v)
        if model_config.get("class"):
            setattr(pretrain_config, "_name_or_path", model_config.get("class"))

    local_data = []
    if len(train_config["datasets"].get("local", [])) > 0:
        local_data.append(build_local_datasets(train_config, tokenizer))

    streaming_data = []
    if train_config["datasets"].get("streaming"):
        for dataset in train_config["datasets"].get("streaming", []):
            streaming_config = config["collections"]["streaming"][dataset.lower()]
            streaming_config["identity_function"] = get_identity
            streaming_data.append(streaming_config)

    # Erase old logs
    train_config["log_path"] = "/data/logs/" + focus
    if fresh_logs == True:
        shutil.rmtree(train_config["log_path"], ignore_errors=True)

    os.makedirs(f"{train_config['log_path']}/{adapter}", exist_ok=True)

    init_kwargs = dict(
        model=launch_model,
        model_folder=model_folder,
        tokenizer=tokenizer,
        config=pretrain_config,
        petals=use_petals,
        cache_dir="/data/models",
        embeddings_dir="/data/embeddings/" + focus,
        tuning_mode=tuning_mode,
        pre_seq_len=pre_seq_len,
        merge_adapters=False,
        precision=train_config.get("precision", model_config.get("precision", 32)),
        device_map=train_config.get(
            "device_map", model_config.get("device_map", "auto")
        ),
    )

    train_config["local_data"] = local_data
    train_config["streaming_data"] = streaming_data

    print("training on the following collections:")
    print(f"local data: {len(local_data)} sets")
    print(f"streaming data: {streaming_data}")

    time.sleep(3)

    if os.environ.get("TASK") == "trial":
        optimize_hparams(init_kwargs, train_config)
        return

    # Instantiate the model object
    prototype = aigen(**init_kwargs)

    if train_type not in ["standard", "pretrain"] and not use_petals:
        output_dir = f"/data/adapters/{focus}/{adapter}"
        if resume:
            prototype.load_adapter(output_dir)
        else:
            prototype.create_adapter(train_config)

    logger = loggers.TensorBoardLogger(
        train_config["log_path"], name=adapter, default_hp_metric=True
    )

    # Train the model
    prototype.train(
        petals=use_petals,
        seed=nist_beacon()[1],
        output_dir=output_dir,
        loggers=[logger],
        **train_config,
    )


# Join every file located in a particular directory
def create_dataset(
    path="/lab",
    tokenizer=None,
    block_size: int = 1024,
    stride: int = 0,
    samples: float = 1.0,
):
    prefixes = [
        ".git",
        "/lab/reaper/logseq",
        "/lab/reaper/assets",
        "/lab/reaper/public",
        "/lab/aigen/aigen/static",
        "/lab/opencog/learn/attic",
        "/lab/opencog/learn/learn-lang-diary",
        "/src/__pycache__",
        "/src/modules/__pycache__",
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
        "png",
        "pt",
        "pyc",
        "related.tex",
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

    for file in files:
        try:
            # Skip files we can't process
            skip = False
            for suffix in suffixes:
                if file.lower().endswith(suffix):
                    skip = True
                    break
            for prefix in prefixes:
                if file.startswith(prefix):
                    skip = True
                    break

            if skip == True:
                continue

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
            with open(intermediate_path, "a") as intermediate:
                intermediate.write(f"failed:{file}{tokenizer.eos_token}")
            print(f"failed: {colors.RED}{file}{colors.WHITE}")
            logging.error(e)

    print(f"tokenizing: {colors.BLUE}{path}{colors.WHITE}")

    dataset = StaticDataset(
        intermediate_path,
        tokenizer=tokenizer,
        batch_size=100000,
        block_size=block_size,
        stride=stride,
        bos_token=tokenizer.bos_token or "<|void|>",
        eos_token=tokenizer.eos_token or "<|void|>",
        unk_token=tokenizer.unk_token or "<|void|>",
        pad_token=tokenizer.pad_token or "<|void|>",
    )

    # Cleanup temp files used for tokenized dataset creation
    if os.path.exists("/tmp/intermediate.txt"):
        os.remove("/tmp/intermediate.txt")

    return dataset


# Create a tokenized dataset from every directory specified in config file
def build_local_datasets(train_config, tokenizer):
    staging = {}
    block_size = train_config.get("block_size")
    stride = train_config.get("stride", 0)
    collections = config["collections"]["local"]
    datasets = train_config["datasets"]["local"]
    for collection in datasets:
        for dataset in collections[collection]:
            if dataset not in staging:
                ds_config = collections[collection][dataset] or {}

                cache_path = f"{focus}/{str(block_size)}/{dataset}"
                hashed = hash_directory("/" + dataset)

                print(f"loading: {colors.BLUE}{cache_path}{colors.WHITE}")

                cached = f"/data/datasets/{cache_path}/{hashed}.tar.gz"

                if os.path.exists(cached):
                    ds = StaticDataset(
                        cached,
                        block_size=block_size,
                        from_cache=True,
                    )
                else:
                    shutil.rmtree(f"/data/datasets/{cache_path}", ignore_errors=True)
                    os.makedirs(f"/data/datasets/{cache_path}", exist_ok=True)

                    ds = create_dataset(
                        path="/" + dataset,
                        tokenizer=tokenizer,
                        block_size=block_size,
                        stride=ds_config.get("stride", stride),
                    )

                    ds.save(cache_destination=cached)

                val_split = ds_config.get("val_split", train_config.get("val_split", 0))
                train_split = 1.0 - val_split

                train_data, val_data = torch.utils.data.random_split(
                    ds, [train_split, val_split]
                )

                weight = ds_config.get("weight", 1.0)
                staging[dataset] = {
                    "train": train_data,
                    "val": val_data,
                    "weight": weight,
                }

            else:
                print(
                    colors.GREEN
                    + dataset
                    + colors.WHITE
                    + " is already loaded into memory"
                )

    # Merge all tokenized datasets into a single dataset for training
    collected_train = []
    collected_val = []
    weights = []
    for collection in staging:
        train_data = staging[collection]["train"]
        val_data = staging[collection]["val"]
        collected_train.append(train_data)
        collected_val.append(val_data)
        weights += [staging[collection]["weight"]] * len(train_data)

    return {
        "train": ConcatDataset(collected_train),
        "val": ConcatDataset(collected_val),
        "weights": weights,
    }


if __name__ == "__main__":
    main()
