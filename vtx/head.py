from aitextgen import aitextgen
from torch import torch
import os
import sys
import re
import time
import random
import requests
import functools
import typing
import asyncio
import gc
import yaml
import logging
from mergedeep import merge, Strategy
import transformers

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

# holds the model globally
ai = None

os.environ["LRU_CACHE_CAPACITY"] = "1"

focus = os.environ["FOCUS"]

ship = ":>"
propulsion = "¶"

# Decorator to a blocking function into a background thread
def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


# Load the specified model
@to_thread
def loader(target=None):

    try:
        del ai
        gc.collect()
    except:
        pass

    if target == None:
        target = focus

    model = config[target]

    if "training" in model:
        model_folder = "gpt/models/" + target
        tokenizer_file = "src." + target + ".tokenizer.json"
    else:
        tokenizer_file = "src." + target + ".tokenizer.json"
        model_folder = None

    print(bc.CORE + "INK@CORE: " + bc.ENDC + model["info"])
    ai = aitextgen(
        model=model.get("model", None),
        model_folder=model_folder,
        # tokenizer_file=tokenizer_file,
        tokenizer_file=None,
        to_gpu=model["to_gpu"],
        cache_dir="gpt/models",
    )
    print(bc.ROOT + "ONE@ROOT: " + bc.ENDC + str(ai))
    return ai


# ping pang pong
context = [
    propulsion + "975174695399854150" + ship + " I am a robot.",
    propulsion + "1051994502333726841" + ship + " I am a ghost",
    propulsion + "806051627198709760" + ship + " i am a human",
    propulsion + "204716337971331072" + ship + " I am a Medium.",
    propulsion + "855529761185857566" + ship + " I am an animal..",
]


# Build a local cache of global conversational state
def build_context(message):
    if len(context) >= 9:
        context.pop(0)
        build_context(message[:111])
    else:
        context.append(propulsion + message[:110])


# Generate a completion from bias and context
@to_thread
def gen(bias=None, ctx=None):

    prompt = propulsion

    if ctx == None:
        ctx = context
    history = "\n".join(ctx) + "\n"

    max_new_tokens = config[focus].get("max_new_tokens", 111)

    # set quantum state
    try:
        q = requests.get(
            "https://qrng.anu.edu.au/API/jsonI.php?length=6&type=uint8"
        ).json()
    except:
        q = {"data": [random.randint(0, 256), random.randint(0, 256)]}

    seed = None
    if q["data"][0] < 32:
        seed = q["data"][0]
        print("quantum seed was set to " + str(seed))

    print(bc.CORE + "INK@CORE " + bc.ENDC + ship + " prompt")

    # bias the prompt
    if bias is not None:
        if (len(str(bias)) == 18) or (len(str(bias)) == 19):
            print(bc.CORE + "INK@CORE " + bc.ENDC + ship + " bias toward " + str(bias))
            prefixes = ["I", "You", ""]
            prompt = propulsion + str(bias) + ship + " " + random.choice(prefixes)

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(propulsion)[0])

    # try to complete the prompt
    # https://huggingface.co/docs/transformers/main_classes/text_generation
    try:
        completion = ai.generate(
            n=1,
            prompt=history + prompt,
            do_sample=True,
            min_length=23,
            max_new_tokens=max_new_tokens,
            temperature=0.888,
            top_k=40,
            top_p=0.9,
            return_as_list=True,
            num_beams=3,
            repetition_penalty=2.0,
            exponential_decay_length_penalty=(23, 1.6),
            no_repeat_ngram_size=2,
            early_stopping=True,
            renormalize_logits=True,
            eos_token_id=eos,
            max_time=59,
            seed=seed,
        )
    except Exception as e:
        print(e)
        return
    try:
        print("\033[92m" + "completion" + "\033[0m")
        generation = completion[0][len(history) :]

        try:
            group = re.search(r"^(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
            output = transformer([group[1], group[2]])
        except:
            pass

        if group[2] == "" or group[3] == "":
            print("generation was not subscriptable")
            return
        output = transformer([group[2], group[3]])
        try:
            output = output.replace("Q:", "")
        except:
            output = output
    except Exception as e:
        print(e)
        output = completion[0]
    return output


# format the output
def transformer(group):
    responses = [
        f'The ghost of <@{group[0]}> suggests, *"{group[1]}"*',
        f'<@{group[0]}> says, *"{group[1]}"*',
        f'<@{group[0]}> would say, *"{group[1]}"*',
        f'They said, *"{group[1]}"*',
        f"{group[1]}",
    ]
    return random.choice(responses)


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
