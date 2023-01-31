from aitextgen.TokenDataset import TokenDataset, merge_datasets
from aitextgen.tokenizers import train_tokenizer
from aitextgen.utils import build_gpt2_config
from aitextgen import aitextgen
from transformers import GPT2Config, GPTNeoConfig
from pytorch_lightning import loggers
import numpy as np
import os
import shutil, tempfile
import yaml
import random
from mergedeep import merge, Strategy
import logging

logging.getLogger("").setLevel(logging.WARNING)

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

os.environ["TOKENIZERS_PARALLELISM"] = "true"

focus = os.environ["FOCUS"]
model = config[focus]
model_folder = "gpt/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

logger = loggers.TensorBoardLogger("/lab/logs", name=focus, version=model["version"])


def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


def join_files(path):

    tmp_path = "/lab/intermediate"

    isExist = os.path.exists(tmp_path)
    if isExist:
        shutil.rmtree(tmp_path)

    os.makedirs(tmp_path)

    files = list_full_paths(path)
    intermediate_path = tmp_path + "/" + str(random.randint(1000000, 9999999)) + ".txt"
    intermediate = open(intermediate_path, "a")
    for file in files:
        try:
            if (
                file.endswith(".bin")
                or file.endswith(".pyc")
                or file.startswith("/vtx/aitextgen")
            ):
                continue
            with open(file, "r") as content:
                string = content.read()
                intermediate.write(string + "\n\n")
        except:
            print("failed to crunch " + file)
    intermediate.close()
    return intermediate_path


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"


if __name__ == "__main__":

    config = None
    base_model = model["training"]["base_model"]
    batch_size = model["training"]["batch_size"]
    gradient_accumulation_steps = model["training"]["gradient_accumulation_steps"]
    num_steps = model["training"]["num_steps"]
    to_gpu = model["training"]["to_gpu"]
    n_gpu = model["n_gpu"]
    learning_rate = model["training"]["learning_rate"]
    weight_decay = model["training"]["weight_decay"]
    warmup_steps = model["training"]["warmup_steps"]
    max_grad_norm = model["training"]["max_grad_norm"]
    freeze_layers = model["training"]["freeze_layers"]
    num_layers_freeze = model["training"]["num_layers_freeze"]

    # vocab_path = "/lab/" + model["training"]["vocab_path"]
    # vocab_size = model["training"]["vocab_size"]
    # train_tokenizer(
    #     files=list_full_paths(vocab_path),
    #     vocab_size=vocab_size,
    #     save_path="./",
    #     prefix="src." + focus,
    #     dropout=model["training"]["dropout"],
    # )

    print("(" + bc.ROOT + "focus" + bc.ENDC + ")")
    print(f"({bc.CORE}ed{bc.ENDC}) on the ({bc.FOLD}{focus}{bc.ENDC})")

    datasets = []
    for dataset in model["training"]["datasets"]:
        line_by_line = False
        if "line_by_line" in dataset:
            line_by_line = dataset["line_by_line"]

        intermediate_file = join_files("/" + dataset)
        print(bc.FOLD + "loading " + dataset + bc.ENDC)
        datasets.append(
            TokenDataset(
                intermediate_file,
                # tokenizer_file=tokenizer_file,
                block_size=model["training"].get("block_size", None),
                line_by_line=line_by_line,
                # from_cache=True,
                # cache_destination="/lab/" + dataset + ".tar.gz",
                # save_cache=True,
            )
        )

    if os.path.exists("/lab/intermediate"):
        shutil.rmtree("/lab/intermediate")

    if os.path.exists("/lab/logs/" + focus):
        shutil.rmtree("/lab/logs/" + focus)

    merged = merge_datasets(datasets, equalize=model["training"]["equalize_datasets"])

    launch_model = base_model

    if model["training"]["resume"] == True:
        launch_model = None
        model_folder = "gpt/models/" + focus
    else:
        model_folder = None
        if os.path.exists("gpt/models/" + focus):
            shutil.rmtree("gpt/models/" + focus)
        os.makedirs("gpt/models/" + focus)

    output_dir = "gpt/models/" + focus

    ai = aitextgen(
        # tokenizer_file=tokenizer_file,
        config=config,
        model=launch_model,
        model_folder=model_folder,
        to_gpu=to_gpu,
        gradient_checkpointing=True,
        padding_side="left",
    )

    ai.train(
        merged,
        from_cache=False,
        padding_side="left",
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
        gradient_accumulation_steps=model["training"].get(
            "gradient_accumulation_steps", 1
        ),
        fp16=False,
        freeze_layers=model["training"].get("freeze_layers", False),
        num_layers_freeze=model["training"].get("num_layer_freeze", 0),
        progress_bar_refresh_rate=1,
        seed=random.randrange(0, 41, 2),
    )
