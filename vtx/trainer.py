import logging
import shutil
import random
import os
import ninja
from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen import aitextgen
from transformers import AutoTokenizer
from pytorch_lightning import loggers
from utils import ad, bc, config, get_quantum_seed, hash_directory, list_full_paths

cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path
os.environ["TOKENIZERS_PARALLELISM"] = "true"

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

focus = os.environ["FOCUS"]
model = config[focus]
model_folder = "models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"


def build_version(version=0):
    while os.path.exists("/gen/logs/" + focus + "/version_" + str(version)):
        version = version + 1
    return version


# Join every file located in a particular directory
def create_dataset(
    path="/vtx",
    tokenizer=None,
    block_size=1024,
    line_by_line=False,
    shuffle=False,
):
    tmp_path = "/tmp/intermediate"

    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)

    os.makedirs(tmp_path)

    prefixes = [
        ".git",
        "/lab/reaper/logseq",
        "/lab/reaper/assets",
        "/lab/reaper/public",
        "/lab/aitextgen/aitextgen/static",
        "/lab/opencog/learn/learn-lang-diary",
        "/vtx/models",
        "/vtx/__pycache__",
        "/vtx/lab/__pycache__",
    ]

    suffixes = [
        "7z",
        "bib",
        "bin",
        "eot",
        "docx",
        "gif",
        "ico",
        "jpg",
        "jpeg",
        "mp3",
        "mp4",
        "odt",
        "pdf",
        "png",
        "pyc",
        "related.tex",
        "resources/content.xml",
        "resources/meta.xml",
        "sqlite",
        "synctex",
        "ttf",
        "woff",
        "woff2",
        "xlsx",
        "zip",
    ]

    files = list_full_paths(path)
    if shuffle:
        random.shuffle(files)

    intermediate_path = tmp_path + "/" + str(random.randint(1000000, 9999999)) + ".txt"

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
                datasets[file] = TokenDataset(
                    file,
                    block_size=block_size,
                    line_by_line=line_by_line,
                    tokenizer=tokenizer,
                )
            else:
                with open(file, "r") as content:
                    with open(intermediate_path, "a") as intermediate:
                        string = content.read()
                        intermediate.write(string + "\n\n")

        except Exception as e:
            print(e)

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
            block_size=block_size,
            line_by_line=line_by_line,
            tokenizer=tokenizer,
        )

    # Cleanup temp files used for tokenized dataset creation
    if os.path.exists("/tmp/intermediate"):
        shutil.rmtree("/tmp/intermediate")

    return dataset


if __name__ == "__main__":
    base_model = model["training"]["base_model"]

    print("(" + bc.ROOT + "focus" + ad.TEXT + ")")
    print(f"({bc.CORE}ed{ad.TEXT}) on the ({bc.FOLD}{focus}{ad.TEXT})")

    launch_model = None
    fresh_logs = False

    # Resume training on an existing model, or start with a fresh base model
    if model["training"]["resume"] == True:
        if os.path.exists("/vtx/models/" + focus + "/pytorch_model.bin") == True:
            model_folder = "models/" + focus
        else:
            launch_model = base_model
            model_folder = None
            fresh_logs = True
    else:
        launch_model = base_model
        model_folder = None
        fresh_logs = True
        if os.path.exists("/vtx/models/" + focus):
            shutil.rmtree("/vtx/models/" + focus)

    # Start with a fresh logs directory
    if fresh_logs == True:
        if os.path.exists("/gen/logs/" + focus):
            shutil.rmtree("/gen/logs/" + focus)

    if os.path.exists("/vtx/models/" + focus) == False:
        os.makedirs("/vtx/models/" + focus)

    output_dir = "models/" + focus

    if "neo" in base_model.lower():
        tokenizer = None
    else:
        tokenizer = AutoTokenizer.from_pretrained(launch_model)

    # Create a tokenized dataset from every directory specified in config file
    def build_inputs(stage):
        datasets = {}
        block_size = stage.get("block_size", 1024)
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
                            + dataset
                            + "/"
                            + str(duplicate)
                            + ad.TEXT
                        )

                        cached = (
                            "/gen/datasets/"
                            + dataset
                            + "/"
                            + str(focus)
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
                                + dataset
                                + "/"
                                + str(focus)
                                + "/"
                                + str(duplicate)
                            )
                        except:
                            pass

                        os.makedirs(
                            "/gen/datasets/"
                            + dataset
                            + "/"
                            + str(focus)
                            + "/"
                            + str(duplicate)
                        )
                        shuffle = False
                        if duplicate > 0:
                            shuffle = True
                        ds = create_dataset(
                            path="/" + dataset,
                            tokenizer=tokenizer,
                            block_size=block_size,
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
        merged = merge_datasets(collected, equalize=stage["equalize_datasets"])
        return merged

    # Instantiate the model object
    ai = aitextgen(
        model=launch_model,
        model_folder=model_folder,
        to_gpu=True,
        cache_dir="models",
        gradient_checkpointing=model["training"].get("gradient_checkpointing", True),
    )

    version = build_version()

    logger = loggers.TensorBoardLogger(
        "/gen/logs", name=focus, version=version, default_hp_metric=True
    )

    # Train the model
    for i, stage in enumerate(model["training"]["stages"]):
        if "dropout" in stage:
            setattr(ai.model.config, "attention_dropout", stage["dropout"])
            setattr(ai.model.config, "embed_dropout", stage["dropout"])
            setattr(ai.model.config, "resid_dropout", stage["dropout"])
            setattr(ai.model.config, "summary_first_dropout", stage["dropout"])
            setattr(ai.model.config, "hidden_dropout", stage["dropout"])
        prune = stage.get("prune", 0.0)
        inputs = build_inputs(stage)
        ai.train(
            train_data=inputs,
            batch_size=stage.get("batch_size", 1),
            num_steps=stage.get("num_steps", 33333),
            generate_every=123,
            save_every=1000,
            n_gpu=1,
            output_dir=output_dir,
            loggers=logger,
            learning_rate=stage.get("learning_rate", 0.005),
            weight_decay=stage.get("weight_decay", 0.01),
            warmup_steps=stage.get("warmup_steps", 0),
            max_grad_norm=stage.get("max_grad_norm", 0.5),
            gradient_accumulation_steps=stage.get("gradient_accumulation_steps", 1),
            train_transformers_only=stage.get("train_transformers_only", False),
            fp16=False,
            freeze_layers=True,
            num_layers_freeze=stage.get("num_layers_freeze", None),
            scheduler=stage.get("scheduler", "get_linear_schedule_with_warmup"),
            num_cycles=stage.get("num_cycles", 0.5),
            progress_bar_refresh_rate=1,
            seed=get_quantum_seed()[1],
            prune=prune,
            stage=i,
        )
