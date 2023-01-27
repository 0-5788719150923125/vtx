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

# holds the model
ai = None

os.environ["LRU_CACHE_CAPACITY"] = "1"

focus = os.environ["FOCUS"]

ship = ":>"
propulsion = "¶"


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


@to_thread
def load_model(target=None):

    try:
        del ai
        gc.collect()
    except:
        pass

    if target == None:
        target = focus

    model = config[target]

    if "training" in model:
        model_folder = "vtx/models/" + target
        tokenizer_file = "src." + target + ".tokenizer.json"
    else:
        tokenizer_file = "src." + target + ".tokenizer.json"
        model_folder = None

    print(model["info"])
    ai = aitextgen(
        model=model.get("model", None),
        model_folder=model_folder,
        # tokenizer_file=tokenizer_file,
        tokenizer_file=None,
        to_gpu=model["to_gpu"],
    )

    print("INFO: " + str(ai))
    return ai


# ping pang pong
context = [
    propulsion + "975174695399854150" + ship + " I am a robot.",
    propulsion + "1051994502333726841" + ship + " I am a ghost.",
    propulsion + "806051627198709760" + ship + " I am a human.",
    propulsion + "204716337971331072" + ship + " I am a medium.",
    propulsion + "855529761185857566" + ship + " I am an animal.",
]


def build_context(message):
    if len(context) >= 9:
        context.pop(0)
        build_context(message)
    else:
        context.append(propulsion + message)


@to_thread
def gen(bias=None, ctx=None):

    prompt = propulsion

    if ctx == None:
        ctx = context
    history = "\n".join(ctx) + "\n"

    max_length = 1024
    if "max_length" in config[focus]:
        max_length = config[focus]["max_length"]

    # set quantum state
    try:
        q = requests.get(
            "https://qrng.anu.edu.au/API/jsonI.php?length=6&type=uint8"
        ).json()
    except:
        q = {"data": [random.randint(0, 256), random.randint(0, 256)]}

    if q["data"][0] < 32:
        seed = q["data"][0]
        print("quantum seed was set to " + str(seed))
    else:
        seed = None

    # bias the prompt
    if bias is not None:
        if (len(str(bias)) == 18) or (len(str(bias)) == 19):
            print("bias toward " + str(bias))
            prefixes = ["I", "You", ""]
            prompt = propulsion + str(bias) + ship + " " + random.choice(prefixes)

    print("\033[92m" + "prompt" + "\033[0m")
    print(history + prompt)

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(propulsion)[0])

    # try to complete the prompt
    # https://huggingface.co/docs/transformers/main_classes/text_generation
    try:
        completion = ai.generate(
            n=1,
            prompt=history + prompt,
            do_sample=True,
            min_length=23,
            max_length=max_length,
            temperature=0.888,
            top_k=40,
            top_p=0.9,
            return_as_list=True,
            num_beams=3,
            repetition_penalty=2.0,
            length_penalty=-0.9,
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
        generation_zero = completion[0][len(history) :]
        print(generation_zero)

        try:
            group = re.search(
                r"^(¶{1})(?:.*)(\d{18,19})(?::>\s*)(.*)(?:\n*)", generation_zero
            )
            output = transformer([group[1], group[2]])
            print("\033[92m" + "group 1" + "\033[0m")
            print(group[1])
            print("\033[92m" + "group 2" + "\033[0m")
            print(group[2])
            print("\033[92m" + "group 3" + "\033[0m")
            print(group[3])
            print("\033[92m" + "group 4" + "\033[0m")
            print(group[4])
        except:
            pass

        if group[2] == "" or group[3] == "":
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
