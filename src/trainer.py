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
    path="/src",
    tokenizer=None,
    block_size: int = 1024,
    stride: int = 16,
    line_by_line=False,
    shuffle=False,
):
    prefixes = [
        ".git",
        "/lab/reaper/logseq",
        "/lab/reaper/assets",
        "/lab/reaper/public",
        "/lab/aigen/aigen/static",
        "/lab/opencog/learn/learn-lang-diary",
        "/src/models",
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
    if shuffle:
        random.shuffle(files)

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
            else:
                print("loading " + str(file))

            if line_by_line == True:
                with open(file, "r") as content:
                    with open("/tmp/lines.txt", "a") as lines:
                        string = content.read()
                        if "<|url|>" in string:
                            mask_token = tokenizer.mask_token
                            if mask_token is None:
                                mask_token = tokenizer.unk_token
                            string = string.replace("<|url|>", mask_token)
                        lines.write(string)
                datasets[file] = TokenDataset(
                    "/tmp/lines.txt",
                    block_size=block_size,
                    line_by_line=line_by_line,
                    tokenizer=tokenizer,
                    stride=stride,
                )
                os.remove("/tmp/lines.txt")
            else:
                with open(file, "r") as content:
                    with open(intermediate_path, "a") as intermediate:
                        string = content.read()
                        if "<|url|>" in string:
                            mask_token = tokenizer.mask_token
                            if mask_token is None:
                                mask_token = tokenizer.unk_token
                            string = string.replace("<|url|>", mask_token)
                        intermediate.write(string + "\n\n")

        except Exception as e:
            logging.error(e)

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
        )

    # Cleanup temp files used for tokenized dataset creation
    if os.path.exists("/tmp/intermediate.txt"):
        os.remove("/tmp/intermediate.txt")

    return dataset


if __name__ == "__main__":
    base_model = model_config["model"]

    print("(" + bc.ROOT + "focus" + ad.TEXT + ")")
    print(f"({bc.CORE}ed{ad.TEXT}) on the ({bc.FOLD}{focus}{ad.TEXT})")

    launch_model = None
    fresh_logs = False
    resume = model_config["training"].get("resume", False)
    if model_config["training"].get("regen", False):
        if os.path.exists("/gen/datasets/" + focus):
            shutil.rmtree("/gen/datasets/" + focus)

    # Resume training on an existing model, or start with a fresh base model
    if resume == True:
        fresh_logs = False
        if not os.path.exists("/src/models/" + focus + "/pytorch_model.bin"):
            launch_model = base_model
            model_folder = None

    else:
        fresh_logs = True
        launch_model = base_model
        model_folder = None
        if os.path.exists("/src/models/" + focus):
            shutil.rmtree("/src/models/" + focus)
        if os.path.exists("/src/embeddings/" + focus):
            shutil.rmtree("/src/embeddings/" + focus)

    # Start with a fresh logs directory
    if fresh_logs == True:
        if os.path.exists("/gen/logs/" + focus):
            shutil.rmtree("/gen/logs/" + focus)

    output_dir = "models/" + focus

    pre_seq_len = 0
    if "peft" in model_config["training"]:
        p = model_config["training"].get("peft")
        if p["type"] == "prefix":
            pre_seq_len = p.get("num_virtual_tokens")

    tuning_mode = None
    peft_config = None
    use_petals = model_config.get("petals", False)
    if "peft" in model_config["training"]:
        output_dir = "adapters/" + focus
        p = model_config["training"].get("peft")
        if resume == True:
            if model_config.get("petals", False):
                if p["type"] == "prefix":
                    output_dir = "/src/embeddings/" + focus
        else:
            if p["type"] == "lora":
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
            elif p["type"] == "adalora":
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
            elif p["type"] == "prompt":
                if use_petals:
                    tuning_mode = "ptune"
                    pre_seq_len = p.get("num_virtual_tokens")
                    output_dir = "/src/embeddings/" + focus
                else:
                    peft_config = PromptTuningConfig(
                        task_type="CAUSAL_LM",
                        num_virtual_tokens=p.get("num_virtual_tokens", 24),
                    )
            elif p["type"] == "prefix":
                if use_petals:
                    tuning_mode = "deep_ptune"
                    pre_seq_len = p.get("num_virtual_tokens")
                    output_dir = "/src/embeddings/" + focus
                else:
                    peft_config = PrefixTuningConfig(
                        task_type="CAUSAL_LM",
                        num_virtual_tokens=p.get("num_virtual_tokens", 24),
                    )

    # Instantiate the model object
    ai = aigen(
        model=launch_model,
        model_folder=model_folder,
        petals=use_petals,
        cache_dir="models",
        embeddings_dir="/src/embeddings/" + focus,
        tuning_mode=tuning_mode,
        pre_seq_len=pre_seq_len,
        precision=model_config.get("precision", None),
        gradient_checkpointing=model_config["training"].get(
            "gradient_checkpointing", True
        ),
    )

    ai.tokenizer = AutoTokenizer.from_pretrained(
        launch_model,
        cache_dir="models",
        padding=False,
        padding_side=model_config["training"].get("padding_side", "left"),
        truncation=True,
    )

    print(ai.tokenizer)

    # Create a tokenized dataset from every directory specified in config file
    def build_inputs(stage):
        datasets = {}
        block_size = stage.get("block_size", ai.model_max_length)
        stride = stage.get("stride", 0)
        for collection in stage["datasets"]:
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
                            "/gen/datasets/"
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
                                "/gen/datasets/"
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
                            "/gen/datasets/"
                            + focus
                            + "/"
                            + dataset
                            + "/"
                            + str(block_size)
                            + "/"
                            + str(duplicate)
                        )
                        shuffle = False
                        if duplicate > 0:
                            shuffle = True
                        ds = create_dataset(
                            path="/" + dataset,
                            tokenizer=ai.tokenizer,
                            block_size=block_size,
                            stride=stride,
                            line_by_line=line_by_line,
                            shuffle=shuffle,
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
        for collection in stage["datasets"]:
            for dataset in config["collections"][collection]:
                duplicate = 0
                while dataset + str(duplicate) in datasets:
                    collected.append(datasets[dataset + str(duplicate)])
                    duplicate = duplicate + 1
        if len(collected) > 1:
            return merge_datasets(
                collected, equalize=stage.get("equalize_datasets", False)
            )
        else:
            return collected[0]

    get_trainable = False
    if "peft" in model_config["training"]:
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

    elif os.path.exists("/src/models/" + focus) == False:
        os.makedirs("/src/models/" + focus)

    for n, p in ai.model.named_parameters():
        if "lora" in n.lower():
            p.requires_grad = True

    logger = loggers.TensorBoardLogger("/gen/logs", name=focus, default_hp_metric=False)

    # Train the model
    for i, stage in enumerate(model_config["training"]["stages"]):
        inputs = build_inputs(stage)
        ai.train(
            train_data=inputs,
            batch_size=stage.get("batch_size", 1),
            num_steps=stage.get("num_steps", 33333),
            generate_every=model_config["training"].get("generate_every", 500),
            save_every=model_config["training"].get("save_every", 1000),
            n_gpu=1,
            output_dir=output_dir,
            loggers=[logger],
            optimizer=stage.get("optimizer", "AdamW"),
            learning_rate=float(stage.get("learning_rate", 0.005)),
            swa_lr=stage.get("swa_lr", None),
            weight_decay=float(stage.get("weight_decay", 0.01)),
            warmup_steps=stage.get("warmup_steps", 0),
            gradient_clip_val=stage.get("gradient_clip_val", 0.5),
            update_period=stage.get("update_period", 10),
            gradient_accumulation_steps=stage.get("gradient_accumulation_steps", 1),
            train_transformers_only=stage.get("train_transformers_only", False),
            num_layers_freeze=stage.get("num_layers_freeze", 0),
            scheduler=stage.get("scheduler", "get_linear_schedule_with_warmup"),
            progress_bar_refresh_rate=1,
            seed=nist_beacon()[1],
            prune=stage.get("prune", 0.0),
            petals=use_petals,
            use_deepspeed=False,
            hivemind=model_config["training"].get("hivemind", False),
            target_batch_size=stage.get("target_batch_size", 8192),
            stage=i,
        )
