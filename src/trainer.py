import logging
import os
import random
import shutil

mode = os.environ.get("DEV_MODE", None)
if mode == "true":
    from lab.aigen.aigen import aigen
    from lab.aigen.aigen.TokenDataset import TokenDataset, merge_datasets
else:
    from aigen import aigen
    from aigen.TokenDataset import TokenDataset, merge_datasets

from peft import (
    AdaLoraConfig,
    IA3Config,
    LoraConfig,
    PeftConfig,
    PeftModel,
    PrefixTuningConfig,
    PromptTuningConfig,
    get_peft_model,
)
from pytorch_lightning import loggers
from transformers import AutoTokenizer

from common import ad, bc, config, focus, hash_directory, list_full_paths, nist_beacon

model_config = config[focus]
model_folder = "models/" + focus


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
        "pdf",
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

    files = [item for item in files if random.random() <= samples]

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
                print("skipping " + bc.CORE + str(file) + ad.TEXT)
                continue

            if line_by_line == True:
                with open(file, "r") as content:
                    with open("/tmp/lines.txt", "a") as lines:
                        lines.write(content.read())
                datasets[file] = TokenDataset(
                    "/tmp/lines.txt",
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
                        string = content.read()
                        intermediate.write(string + f"\n{tokenizer.eos_token}\n")

        except Exception as e:
            logging.error(e)

    print(f"Tokenizing: {path}")

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


if __name__ == "__main__":
    p = model_config["training"]
    train_type = p.get("type", "standard")
    base_model = model_config["model"]

    print("(" + bc.ROOT + "focus" + ad.TEXT + ")")
    print(f"({bc.CORE}ed{ad.TEXT}) on the ({bc.FOLD}{focus}{ad.TEXT})")

    launch_model = None
    fresh_logs = False
    resume = p.get("resume", False)
    use_petals = model_config.get("petals", False)
    use_hivemind = model_config.get("hivemind", False)
    adapter = p.get("name", "base")

    if p.get("regen", False):
        if os.path.exists("/data/datasets/" + focus):
            shutil.rmtree("/data/datasets/" + focus)

    # Resume training on an existing model, or start with a fresh base model
    if resume == True:
        fresh_logs = False
        if not os.path.exists("/data/models/" + focus + "/pytorch_model.bin"):
            launch_model = base_model
            model_folder = None

    else:
        fresh_logs = True
        launch_model = base_model
        model_folder = None
        if os.path.exists("/data/models/" + focus):
            shutil.rmtree("/data/models/" + focus)
        if os.path.exists("/data/embeddings/" + focus):
            shutil.rmtree("/data/embeddings/" + focus)

    # Start with a fresh logs directory
    if fresh_logs == True:
        if os.path.exists("/data/logs/" + focus + "/" + adapter):
            shutil.rmtree("/data/logs/" + focus + "/" + adapter)

    tuning_mode = None
    peft_config = None
    pre_seq_len = 0
    output_dir = "/data/adapters/" + focus + "/" + adapter
    if train_type == "lora":
        peft_config = LoraConfig(
            task_type="CAUSAL_LM",
            r=p.get("r", 4),
            lora_alpha=p.get("alpha", 16),
            lora_dropout=p.get("dropout", 0.1),
            bias=p.get("bias", "none"),
            target_modules=p.get("target_modules", None),
            rank_pattern=p.get("rank_pattern", {}),
            alpha_pattern=p.get("alpha_pattern", {}),
            modules_to_save=p.get("modules_to_save", None),
        )
    elif train_type == "adalora":
        peft_config = LoraConfig(
            task_type="CAUSAL_LM",
            r=p.get("r", 4),
            lora_alpha=p.get("alpha", 16),
            lora_dropout=p.get("dropout", 0.1),
            bias=p.get("bias", "none"),
            target_modules=p.get("target_modules", None),
            rank_pattern=p.get("rank_pattern", {}),
            alpha_pattern=p.get("alpha_pattern", {}),
            modules_to_save=p.get("modules_to_save", None),
        )
    elif train_type == "ia3":
        peft_config = IA3Config(
            task_type="CAUSAL_LM",
            target_modules=p.get("target_modules", None),
            feedforward_modules=p.get("feedforward_modules", None),
        )
    elif train_type == "prompt":
        if use_petals:
            tuning_mode = "ptune"
            pre_seq_len = p.get("num_virtual_tokens")
            output_dir = "/data/embeddings/" + focus
        else:
            peft_config = PromptTuningConfig(
                task_type="CAUSAL_LM",
                num_virtual_tokens=p.get("num_virtual_tokens", 24),
            )
    elif train_type == "prefix":
        if use_petals:
            tuning_mode = "deep_ptune"
            pre_seq_len = p.get("num_virtual_tokens")
            output_dir = "/data/embeddings/" + focus
        else:
            peft_config = PrefixTuningConfig(
                task_type="CAUSAL_LM",
                num_virtual_tokens=p.get("num_virtual_tokens", 24),
            )
    else:
        output_dir = "/data/models/" + focus

    # Instantiate the model object
    ai = aigen(
        model=launch_model,
        model_folder=model_folder,
        petals=use_petals,
        cache_dir="/data/models",
        embeddings_dir="/data/embeddings/" + focus,
        tuning_mode=tuning_mode,
        pre_seq_len=pre_seq_len,
        precision=model_config.get("precision", None),
        gradient_checkpointing=p.get("gradient_checkpointing", True),
    )

    ai.tokenizer = AutoTokenizer.from_pretrained(
        launch_model,
        cache_dir="/data/models",
        padding="max_length",
        padding_side=p.get("padding_side", "left"),
        return_overflowing_tokens=True,
        truncation=True,
    )
    if ai.tokenizer.pad_token is None:
        ai.tokenizer.pad_token = ai.tokenizer.eos_token

    print(ai.tokenizer)

    # Create a tokenized dataset from every directory specified in config file
    def build_inputs(c):
        datasets = {}
        block_size = c.get("block_size", ai.model_max_length)
        stride = c.get("stride", 0)
        for collection in c["datasets"]:
            for dataset in config["collections"][collection]:
                if dataset not in datasets:
                    line_by_line = False
                    duplicate = 0
                    if config["collections"][collection][dataset] is not None:
                        if "line_by_line" in config["collections"][collection][dataset]:
                            line_by_line = config["collections"][collection][
                                dataset
                            ].get("line_by_line", False)
                        if "duplicate" in config["collections"][collection][dataset]:
                            duplicate = config["collections"][collection][dataset].get(
                                "duplicate", 0
                            )

                    while duplicate >= 0:
                        print(
                            "loading "
                            + bc.FOLD
                            + focus
                            + "/"
                            + dataset
                            + "/"
                            + str(block_size)
                            + "/"
                            + str(duplicate)
                            + ad.TEXT
                        )

                        cached = (
                            "/data/datasets/"
                            + focus
                            + "/"
                            + dataset
                            + "/"
                            + str(block_size)
                            + "/"
                            + str(duplicate)
                            + "/"
                            + hash_directory("/" + dataset)
                            + ".tar.gz"
                        )

                        if os.path.exists(cached):
                            datasets[dataset + str(duplicate)] = TokenDataset(
                                cached,
                                block_size=block_size,
                                from_cache=True,
                            )
                            duplicate = duplicate - 1
                            continue

                        try:
                            shutil.rmtree(
                                "/data/datasets/"
                                + focus
                                + "/"
                                + dataset
                                + "/"
                                + str(block_size)
                                + "/"
                                + str(duplicate)
                            )
                        except:
                            pass

                        os.makedirs(
                            "/data/datasets/"
                            + focus
                            + "/"
                            + dataset
                            + "/"
                            + str(block_size)
                            + "/"
                            + str(duplicate)
                        )
                        samples = 1.0
                        if config["collections"][collection][dataset] is not None:
                            stride = config["collections"][collection][dataset].get(
                                "stride", stride
                            )
                            samples = config["collections"][collection][dataset].get(
                                "samples", samples
                            )
                        ds = create_dataset(
                            path="/" + dataset,
                            tokenizer=ai.tokenizer,
                            block_size=block_size,
                            stride=stride,
                            samples=samples,
                            line_by_line=line_by_line,
                        )

                        ds.save(cache_destination=cached)

                        datasets[dataset + str(duplicate)] = ds

                        duplicate = duplicate - 1

                else:
                    print(
                        bc.ROOT + dataset + ad.text + " is already loaded into memory"
                    )

        # Merge all tokenized datasets into a single dataset for training
        collected = []
        for collection in c["datasets"]:
            for dataset in config["collections"][collection]:
                duplicate = 0
                while dataset + str(duplicate) in datasets:
                    collected.append(datasets[dataset + str(duplicate)])
                    duplicate = duplicate + 1
        if len(collected) > 1:
            return merge_datasets(collected, equalize=c.get("equalize_datasets", False))
        else:
            return collected[0]

    get_trainable = False
    if train_type != "standard":
        if not use_petals:
            get_trainable = True
            if resume == True:
                ai.model = PeftModel.from_pretrained(ai.model, output_dir)
                setattr(ai.model.config, "is_prompt_learning", False)
                setattr(ai.model.config, "is_trainable", True)
            else:
                ai.model = get_peft_model(ai.model, peft_config)

    print(ai.model)
    if get_trainable:
        ai.model.print_trainable_parameters()

    elif os.path.exists("/data/models/" + focus + "/" + adapter) == False:
        os.makedirs("/data/models/" + focus + "/" + adapter)

    for name, param in ai.model.named_parameters():
        if "lora" in name.lower():
            param.requires_grad = True

    logger = loggers.TensorBoardLogger(
        "/data/logs", name=focus + "/" + adapter, default_hp_metric=True
    )

    train_data = build_inputs(p)
    print("Final dataset:")
    print(train_data)

    # Train the model
    ai.train(
        train_data=train_data,
        n_gpu=1,
        benchmark=False,
        petals=use_petals,
        hivemind=use_hivemind,
        seed=nist_beacon()[1],
        output_dir=output_dir,
        loggers=[logger],
        batch_size=p.get("batch_size", 1),
        num_steps=p.get("num_steps", 33333),
        generate_every=p.get("generate_every", 500),
        save_every=p.get("save_every", 1000),
        optimizer=p.get("optimizer", "AdamW"),
        learning_rate=float(p.get("learning_rate", 0.005)),
        swa_lr=p.get("swa_lr", None),
        weight_decay=float(p.get("weight_decay", 0.01)),
        warmup_steps=p.get("warmup_steps", 0),
        gradient_clip_val=p.get("gradient_clip_val", 0.5),
        update_period=p.get("update_period", 10),
        gradient_accumulation_steps=p.get("gradient_accumulation_steps", 1),
        train_transformers_only=p.get("train_transformers_only", False),
        num_layers_freeze=p.get("num_layers_freeze", 0),
        scheduler=p.get("scheduler", "get_linear_schedule_with_warmup"),
        prune=p.get("prune", 0.0),
        target_batch_size=p.get("target_batch_size", 8192),
        val_split=p.get("val_split", 0.0),
        val_interval=p.get("val_interval", 1000),
    )
