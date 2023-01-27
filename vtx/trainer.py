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

with open("/vtx/defaults.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        # pprint.pprint(config)
except:
    config = default_config

os.environ["TOKENIZERS_PARALLELISM"] = "true"

focus = os.environ["FOCUS"]
model = config[focus]
model_folder = "vtx/models/" + focus
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
        with open(file, "r") as content:
            string = content.read()
            intermediate.write(string + "\n\n")
    intermediate.close()
    return intermediate_path


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

    print("\033[91m" + "focus" + "\033[0m")
    print("\033[91m" + "ed on the " + focus + "\033[0m")

    datasets = []
    for dataset in model["training"]["datasets"]:
        line_by_line = False
        if "line_by_line" in dataset:
            line_by_line = dataset["line_by_line"]

        intermediate_file = join_files("/lab/" + dataset)
        datasets.append(
            TokenDataset(
                intermediate_file,
                # tokenizer_file=tokenizer_file,
                block_size=model["training"].get("block_size", None),
                line_by_line=line_by_line,
            )
        )

    merged = merge_datasets(datasets, equalize=model["training"]["equalize_datasets"])

    ai = aitextgen(
        # tokenizer_file=tokenizer_file,
        config=config,
        model=base_model,
        to_gpu=to_gpu,
        gradient_checkpointing=True,
    )

    ai.train(
        merged,
        from_cache=False,
        batch_size=batch_size,
        num_steps=num_steps,
        generate_every=250,
        save_every=1000,
        n_gpu=n_gpu,
        output_dir=model_folder,
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
        seed=41,
    )
