import logging
import shutil
import random
import os
from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen import aitextgen
from transformers import GPT2Config, GPTNeoConfig
from pytorch_lightning import loggers
from utils import ad, bc, config

os.environ["TOKENIZERS_PARALLELISM"] = "true"

focus = os.environ["FOCUS"]
model = config[focus]
model_folder = "models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"


def build_version(version=0):
    if os.path.exists("/gen/logs/" + focus + "/version_" + str(version)):
        version = version + 1
        return build_version(version)
    return version


version = build_version()

logger = loggers.TensorBoardLogger(
    "/gen/logs", name=focus, version=version, default_hp_metric=False
)

# Get the full path to every file in a directory
def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


# Join every file located in a particular directory
def join_files(path):

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
    intermediate_path = tmp_path + "/" + str(random.randint(1000000, 9999999)) + ".txt"
    intermediate = open(intermediate_path, "a")
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
                continue

            with open(file, "r") as content:
                string = content.read()
                intermediate.write(string + "\n\n")
        except:
            print("failed to crunch " + file)
    intermediate.close()
    return intermediate_path


if __name__ == "__main__":

    # Poorly-load configs
    base_model = model["training"]["base_model"]
    to_gpu = model["training"]["to_gpu"]
    n_gpu = model["n_gpu"]
    warmup_steps = model["training"]["warmup_steps"]
    freeze_layers = model["training"]["freeze_layers"]

    print("(" + bc.ROOT + "focus" + ad.TEXT + ")")
    print(f"({bc.CORE}ed{ad.TEXT}) on the ({bc.FOLD}{focus}{ad.TEXT})")

    fresh_logs = False

    # Resume training on an existing model, or start with a fresh base model
    if model["training"]["resume"] == True:
        if os.path.exists("/vtx/models/" + focus + "/pytorch_model.bin") == True:
            launch_model = None
            model_folder = "models/" + focus
        else:
            model_folder = None
            fresh_logs = True
    else:
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

    # Create a tokenized dataset from every directory specified in config file
    datasets = {}
    inputs = []
    learning_rate = []
    num_steps = []
    num_layers_freeze = []
    weight_decay = []
    max_grad_norm = []
    batch_size = []
    gradient_accumulation_steps = []
    for stage in model["training"]["stages"]:
        learning_rate.append(stage["learning_rate"])
        num_steps.append(stage["num_steps"])
        num_layers_freeze.append(stage["num_layers_freeze"])
        weight_decay.append(stage["weight_decay"])
        max_grad_norm.append(stage["max_grad_norm"])
        batch_size.append(stage["batch_size"])
        gradient_accumulation_steps.append(stage["gradient_accumulation_steps"])
        for collection in stage["datasets"]:
            for dataset in config["collections"][collection]:
                if dataset not in datasets:
                    line_by_line = False
                    if "line_by_line" in dataset:
                        line_by_line = dataset["line_by_line"]

                    intermediate_file = join_files("/" + dataset)
                    print(bc.FOLD + "loading " + dataset + ad.TEXT)

                    datasets[dataset] = TokenDataset(
                        intermediate_file,
                        block_size=model["training"].get("block_size", None),
                        line_by_line=line_by_line,
                    )
                else:
                    print(
                        bc.ROOT + dataset + " is already loaded into memory" + ad.TEXT
                    )

        # Merge all tokenized datasets into a single dataset for training
        collected = []
        for collection in stage["datasets"]:
            for dataset in config["collections"][collection]:
                if dataset in datasets:
                    collected.append(datasets[dataset])
        merged = merge_datasets(
            collected, equalize=model["training"]["equalize_datasets"]
        )
        inputs.append(merged)

    # Cleanup temp files used for tokenized dataset creation
    if os.path.exists("/tmp/intermediate"):
        shutil.rmtree("/tmp/intermediate")

    launch_model = base_model

    # Instantiate the model object
    ai = aitextgen(
        model=launch_model,
        model_folder=model_folder,
        to_gpu=to_gpu,
        gradient_checkpointing=True,
        cache_dir="models",
    )

    # Train the model
    ai.cross_train(
        inputs=inputs,
        from_cache=False,
        batch_size=batch_size,
        num_steps=num_steps,
        generate_every=333,
        save_every=1000,
        n_gpu=n_gpu,
        output_dir=output_dir,
        loggers=logger,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        warmup_steps=warmup_steps,
        max_grad_norm=max_grad_norm,
        gradient_accumulation_steps=gradient_accumulation_steps,
        fp16=False,
        freeze_layers=model["training"].get("freeze_layers", False),
        num_layers_freeze=num_layers_freeze,
        progress_bar_refresh_rate=1,
        seed=random.randint(0, 2**32 - 1),
    )
