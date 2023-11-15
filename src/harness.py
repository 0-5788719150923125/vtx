import logging
import math
import os
import random
import shutil
import time

from lightning.pytorch import loggers
from moduleformer import (
    ModuleFormerConfig,
    ModuleFormerForCausalLM,
    ModuleFormerForSequenceClassification,
)
from peft import (
    AdaLoraConfig,
    IA3Config,
    LoKrConfig,
    LoraConfig,
    PeftConfig,
    PeftModel,
    PrefixTuningConfig,
    PromptTuningConfig,
    get_peft_model,
)
from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from aigen import aigen
from aigen.TokenDataset import TokenDataset, merge_datasets
from common import ad, bc, config, focus, hash_directory, list_full_paths, nist_beacon

AutoConfig.register("moduleformer", ModuleFormerConfig)
AutoModelForCausalLM.register(ModuleFormerConfig, ModuleFormerForCausalLM)
AutoModelForSequenceClassification.register(
    ModuleFormerConfig, ModuleFormerForSequenceClassification
)

model_config = config[focus]
model_folder = "models/" + focus

os.environ["TOKENIZERS_PARALLELISM"] = "false"


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
                print(f"skipping: {bc.CORE}{file}{ad.TEXT}")
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
                        string = content.read()
                        intermediate.write(string + f"\n{tokenizer.eos_token}\n")

        except Exception as e:
            print(f"failed: {bc.CORE}{file}{ad.TEXT}")
            logging.error(e)

    print(f"tokenizing: {bc.FOLD}{path}{ad.TEXT}")

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


if __name__ == "__main__":
    p = model_config["training"]
    train_type = p.get("type", "standard")
    base_model = model_config["model"]

    print("(" + bc.ROOT + "focus" + ad.TEXT + ")")
    time.sleep(2)
    print(f"({bc.CORE}ed{ad.TEXT}) on the ({bc.FOLD}{focus}{ad.TEXT})")
    time.sleep(3)

    launch_model = None
    fresh_logs = False
    resume = p.get("resume", False)
    use_petals = model_config.get("petals", False)
    use_hivemind = model_config.get("hivemind", False)
    adapter = p.get("name", "base")

    regen = p.get("regen", False)
    if regen:
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
    pretrain_config = None
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
        peft_config = AdaLoraConfig(
            task_type="CAUSAL_LM",
            r=p.get("r", 4),
            init_r=p.get("init_r", 12),
            target_r=p.get("target_r", 8),
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
    elif train_type == "lokr":
        peft_config = LoKrConfig(
            task_type="CAUSAL_LM",
            r=p.get("r", 4),
            alpha=p.get("alpha", 16),
            rank_dropout=p.get("dropout", 0.0),
            module_dropout=p.get("dropout", 0.0),
            use_effective_conv2d=False,
            decompose_both=False,
            decompose_factor=1,
            target_modules=p.get("target_modules", None),
            rank_pattern=p.get("rank_pattern", {}),
            alpha_pattern=p.get("alpha_pattern", {}),
            modules_to_save=p.get("modules_to_save", None),
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

    # Create a tokenized dataset from every directory specified in config file
    def build_inputs(c, tokenizer):
        datasets = {}
        block_size = c.get("block_size")
        assert block_size, "You must set a block_size to use."
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

                    cache_path = f"{focus}/{dataset}/{str(block_size)}"
                    hashed = hash_directory("/" + dataset)
                    while duplicate >= 0:
                        new_path = f"{cache_path}/{str(duplicate)}"
                        print(f"loading: {bc.FOLD}{new_path}{ad.TEXT}")

                        cached = f"/data/datasets/{new_path}/{hashed}.tar.gz"

                        if os.path.exists(cached):
                            datasets[dataset + str(duplicate)] = TokenDataset(
                                cached,
                                block_size=block_size,
                                from_cache=True,
                            )
                            duplicate -= 1
                            continue

                        try:
                            shutil.rmtree(f"/data/datasets/{new_path}")
                        except:
                            pass

                        os.makedirs(f"/data/datasets/{new_path}")
                        samples = 1.0
                        if config["collections"][collection][dataset] is not None:
                            dataset_config = config["collections"][collection][dataset]
                            stride = dataset_config.get("stride", stride)
                            samples = dataset_config.get("samples", samples)
                        ds = create_dataset(
                            path="/" + dataset,
                            tokenizer=tokenizer,
                            block_size=block_size,
                            stride=stride,
                            samples=samples,
                            line_by_line=line_by_line,
                        )

                        ds.save(cache_destination=cached)

                        datasets[dataset + str(duplicate)] = ds

                        duplicate -= 1

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

    device_map = "auto"

    tokenizer = AutoTokenizer.from_pretrained(
        launch_model,
        cache_dir="/data/models",
        padding="max_length",
        padding_side=p.get("padding_side", "left"),
        use_fast=True,
        return_overflowing_tokens=True,
        truncation=True,
        trust_remote_code=True,
    )

    # extended = False
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    #     tokenizer.add_special_tokens({"pad_token": str(tokenizer.eos_token)})
    #     extended = True

    print(tokenizer)

    train_data = build_inputs(p, tokenizer)

    if train_type == "pretrain":
        pretrain_config = AutoConfig.from_pretrained(launch_model)
        print(f"{bc.CORE}original pretrain config:{ad.TEXT}")
        print(pretrain_config)
        setattr(pretrain_config, "_name_or_path", focus)
        for k, v in p.get("overrides").items():
            setattr(pretrain_config, k, v)
        print(f"{bc.ROOT}modified pretrain config:{ad.TEXT}")
        print(pretrain_config)

    # Instantiate the model object
    prototype = aigen(
        model=launch_model,
        model_folder=model_folder,
        config=pretrain_config,
        petals=use_petals,
        cache_dir="/data/models",
        embeddings_dir="/data/embeddings/" + focus,
        tuning_mode=tuning_mode,
        pre_seq_len=pre_seq_len,
        precision=model_config.get("precision", None),
        gradient_checkpointing=p.get("gradient_checkpointing", True),
        device_map=device_map,
    )

    prototype.tokenizer = tokenizer

    # if extended:
    #     prototype.model.resize_token_embeddings(len(prototype.tokenizer))

    get_trainable = False
    if train_type not in ["standard", "pretrain"]:
        if not use_petals:
            get_trainable = True
            if resume == True:
                try:
                    prototype.model = PeftModel.from_pretrained(
                        prototype.model, output_dir
                    )
                except Exception as e:
                    print(prototype.model)
                    print(e)
                assert isinstance(
                    prototype.model, PeftModel
                ), "Failed to convert prototype into a PeftModel."
                setattr(prototype.model.config, "is_prompt_learning", False)
                setattr(prototype.model.config, "is_trainable", True)
            else:
                prototype.model = get_peft_model(prototype.model, peft_config)

    print(prototype.model)
    if get_trainable:
        prototype.model.print_trainable_parameters()

    elif os.path.exists("/data/models/" + focus + "/" + adapter) == False:
        os.makedirs("/data/models/" + focus + "/" + adapter)

    for name, param in prototype.model.named_parameters():
        if "lora" in name.lower() or "lokr" in name.lower() or "ia3" in name.lower():
            param.requires_grad = True

    logger = loggers.TensorBoardLogger(
        f"/data/logs/{focus}", name=adapter, default_hp_metric=True
    )

    block_size = p.get("block_size", 2048)

    print(
        f"Final dataset: {bc.ROOT}{len(train_data)}{ad.TEXT} batches, {bc.ROOT}{len(train_data) * block_size}{ad.TEXT} tokens"
    )

    val_interval = p.get("val_interval", 1000)
    if val_interval > len(train_data):
        val_interval = math.floor(len(train_data) / 10)

    # Train the model
    prototype.train(
        train_data=train_data,
        n_gpu=1,
        benchmark=False,
        petals=use_petals,
        hivemind=use_hivemind,
        deepspeed=p.get("deepspeed", False),
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
        num_cycles=p.get("num_cycles", None),
        prune=p.get("prune", 0.0),
        target_batch_size=p.get("target_batch_size", 8192),
        block_size=block_size,
        val_split=p.get("val_split", 0.0),
        val_interval=val_interval,
        supplement=p.get("supplement", False),
    )