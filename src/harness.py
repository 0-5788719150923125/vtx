import logging
import os
import random
import re
import shutil
import time

from lightning.pytorch import loggers
from pypdf import PdfReader
from tokenizers import Tokenizer
from transformers import AutoConfig, AutoTokenizer, PreTrainedTokenizerFast

from aigen.aigen import aigen
from aigen.aigen.datasets import StaticDataset, merge_datasets
from aigen.aigen.tokenizers import train_tokenizer
from aigen.aigen.tuners import optimize_hparams
from common import colors, config, focus, hash_directory, list_full_paths, nist_beacon
from extensions import register_models

register_models()

verbose = True
local_rank = int(os.environ.get("LOCAL_RANK", 0))
world_rank = int(os.environ.get("WORLD_RANK", 0))

if local_rank > 0:
    verbose = False

model_config = config[focus]
train_config = model_config["training"]


def main():
    if verbose:
        print("(" + colors.GREEN + "focus" + colors.WHITE + ")")
        time.sleep(2)
        print(
            f"({colors.RED}ed{colors.WHITE}) on the ({colors.BLUE}{focus}{colors.WHITE})"
        )
        time.sleep(3)

    base_model = model_config["model"]
    model_folder = "/data/models/" + focus
    launch_model = None
    fresh_logs = False
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

    if train_config.get("tokenizer") is not None:
        tokenizer_file = f"/data/tokenizers/{focus}/tokenizer.json"
        if not os.path.exists(tokenizer_file):
            train_tokenizer(
                files=list_full_paths("/lab/research"),
                dropout=0.9,
                vocab_size=train_config["overrides"].get("vocab_size"),
                min_frequency=2,
                save_path=f"/data/tokenizers",
                prefix=focus,
                serialize=True,
                trim_offsets=True,
            )
        tokenizer = PreTrainedTokenizerFast(
            tokenizer_file=tokenizer_file,
            bos_token="<|endoftext|>",
            eos_token="<|endoftext|>",
            unk_token="<|endoftext|>",
            pad_token="<|endoftext|>",
            **tokenizer_config,
        )
    else:
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_model, **tokenizer_config)

    if hasattr(tokenizer, "pad_token") and tokenizer.pad_token is None:
        setattr(tokenizer, "pad_token", tokenizer.eos_token)

    if verbose:
        print(tokenizer)

    if train_type == "pretrain" and not resume:
        pretrain_config = AutoConfig.from_pretrained(launch_model)
        if verbose:
            print(f"{colors.RED}original pretrain config:{colors.WHITE}")
            print(pretrain_config)
        setattr(pretrain_config, "_name_or_path", focus)
        setattr(pretrain_config, "bos_token_id", tokenizer.bos_token_id)
        setattr(pretrain_config, "eos_token_id", tokenizer.eos_token_id)
        for k, v in train_config.get("overrides").items():
            setattr(pretrain_config, k, v)
        if verbose:
            print(f"{colors.GREEN}modified pretrain config:{colors.WHITE}")
            print(pretrain_config)

    static_data = []
    if len(train_config["datasets"].get("static", [])) > 0:
        static_data.append(build_static_datasets(train_config, tokenizer))

    streaming_data = []
    for dataset in train_config["datasets"].get("streaming", []):
        streaming_data.append(config["collections"]["streaming"][dataset.lower()])

    # Erase old logs
    log_path = "/data/logs/" + focus
    train_config["log_path"] = log_path
    if fresh_logs == True:
        shutil.rmtree(log_path, ignore_errors=True)

    os.makedirs(f"{log_path}/{adapter}", exist_ok=True)

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
        precision=model_config.get("precision", 32),
        device_map=model_config.get("device_map", "auto"),
    )

    train_config["static_data"] = static_data
    train_config["streaming_data"] = streaming_data

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

    logger = loggers.TensorBoardLogger(log_path, name=adapter, default_hp_metric=True)

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
                datasets[file] = StaticDataset(
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
        dataset = StaticDataset(
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
def build_static_datasets(train_config, tokenizer):
    datasets = {}
    block_size = train_config.get("block_size")
    stride = train_config.get("stride", 0)
    for collection in train_config["datasets"]["static"]:
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
                        datasets[dataset + str(duplicate)] = StaticDataset(
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
    for collection in train_config["datasets"]["static"]:
        for dataset in config["collections"]["static"][collection]:
            duplicate = 0
            while dataset + str(duplicate) in datasets:
                collected.append(datasets[dataset + str(duplicate)])
                duplicate = duplicate + 1
    if len(collected) > 1:
        return merge_datasets(
            collected, equalize=train_config.get("equalize_datasets", False)
        )
    else:
        return collected[0]


if __name__ == "__main__":
    main()
