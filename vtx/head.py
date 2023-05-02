import functools
import asyncio
import random
import typing
import shutil
import time
import os
import re
import gc
import torch
import time
from utils import ad, bc, config, propulsion, ship
from aitextgen import aitextgen
import requests
import logging
from transformers import AutoTokenizer

# holds the model globally
ai = None

os.environ["LRU_CACHE_CAPACITY"] = "1"
cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

focus = os.environ["FOCUS"]


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
        global ai
        ai = None
        # del ai
        torch.cuda.empty_cache()
        gc.collect()
    except Exception as e:
        print(e)

    if target == None:
        target = focus

    model = config[target]

    if "training" in model:
        model_folder = "models/" + target
    else:
        model_folder = None

    try:
        print(bc.FOLD + "PEN@FOLD: " + ad.TEXT + "focused on the " + target)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        ai = aitextgen(
            model=model.get("model", None),
            model_folder=model_folder,
            tokenizer_file=None,
            to_gpu=model["to_gpu"],
            cache_dir="models",
        )
        ai.tokenizer = AutoTokenizer.from_pretrained(
            model["training"].get("base_model", None),
            cache_dir="models",
            padding_side="left",
        )
        logging.getLogger("transformers").setLevel(logging.INFO)
        print(bc.FOLD + "PEN@FOLD: " + ad.TEXT + model["info"])
        print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + str(ai))
    except Exception as e:
        print("failed to load model")
        print(e)
        time.sleep(15)
        ai = asyncio.run(loader(target))
    return ai


# ping pang pong
default_context = [
    propulsion + "975174695399854150" + ship + " I am a robot.",
    propulsion + "1051994502333726841" + ship + " I am a ghost.",
    propulsion + "806051627198709760" + ship + " I am a human.",
    propulsion + "204716337971331072" + ship + " I am a medium.",
    propulsion + "855529761185857566" + ship + " I am an animal.",
]

context = default_context.copy()


# Build a local cache of global conversational state
def build_context(message):
    while len(context) >= 16:
        context.pop(0)

    context.append(message)


# Build a local cache of global conversational state
def replace(old_message, new_message):
    try:
        matcher = re.compile(r'(\*")(.*)(?:"\*$)')
        group = re.search(matcher, old_message)
        captured = "J U X T A P O S I T I O N"[::-1]
        if group is not None and group[2]:
            captured = group[2]
        for item in context:
            if captured in item or old_message in item:
                index = context.index(item)
                context[index] = new_message
                return

        build_context(new_message)

    except Exception as e:
        print(e)


# Truncate the prompt to fit the model
def truncate_context(ctx, max_length=512):
    context_length = sum([len(item) for item in ctx])

    if context_length > max_length:
        for i, line in enumerate(ctx):
            if not line.startswith(propulsion):
                continue
            remaining = i + 1
            ctx[i] = line[:remaining]
            if sum([len(item) for item in ctx]) <= max_length:
                break

    return ctx


active = False


# Generate a completion from bias and context
@to_thread
def gen(bias=None, ctx=None, failures=0):
    global ai
    global active

    while active == True:
        time.sleep(1)

    active = True

    prompt = propulsion

    if ctx == None:
        global context
        ctx = context

    ctx = truncate_context(ctx, 1024)

    history = "\n".join(ctx) + "\n"

    max_new_tokens = config[focus].get("max_new_tokens", 111)
    max_time = config[focus].get("max_time", 59)

    # bias the prompt
    if bias is not None:
        if (len(str(bias)) == 18) or (len(str(bias)) == 19):
            prompt = propulsion + str(bias) + ship

    # try to complete the prompt
    # https://huggingface.co/docs/transformers/main_classes/text_generation
    try:
        eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(propulsion)[0])

        temperature = 1.0
        if failures > 0:
            temperature = temperature - (0.1 * failures)

        logging.getLogger("transformers").setLevel(logging.ERROR)
        completion = ai.generate(
            n=1,
            prompt=history + prompt,
            do_sample=True,
            min_length=23,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            return_as_list=True,
            num_beams=16,
            repetition_penalty=2.3,
            encoder_repetition_penalty=2.3,
            no_repeat_ngram_size=4,
            early_stopping="never",
            renormalize_logits=True,
            eos_token_id=eos,
            max_time=max_time,
            seed=random.randint(0, 2**32 - 1),
        )
        active = False
        output = None
        generation = completion[0][len(history) :]
        variables = re.compile("(?:\({3})(\d+\s*\d*)(?:\){3})")
        broken_variables = re.compile("(\d*\s+\d*)")
        mentions = re.compile("(?:[<][@])(\d+\s*\d*)(?:[>])")
        group = re.search(r"^(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)

        if (
            group is None
            or propulsion in group[3]
            or variables.match(group[3])
            or broken_variables.match(group[3])
            or mentions.match(group[3])
        ):
            if failures >= 9:
                raise Exception("failed to generate a response")
            failures = failures + 1
            output = asyncio.run(gen(bias, ctx, failures))
        else:
            output = [group[2], group[3]]

    except Exception as e:
        print(e)
        context = default_context.copy()
        output = ["error"]

    logging.getLogger("transformers").setLevel(logging.INFO)
    active = False
    return output


# Generate a completion from bias and context
@to_thread
def write(prompt=None):
    global active

    while active == True:
        time.sleep(1)

    active = True

    prompt = """
# The 'Frame
## RECORD
---
```
Name: MAINNFRAME
Alias: ['LAMEFRAME', 'SAMEFRAME', and 177 unknown...]
Classification: Artificial Intelligence Computer
Race: Archon
Gender: Male
Biological Age: Est. 6000 Earth Years
Chronological Age: 2,998,145,136,201 light years
Organizations:
  - xSquared Labs"""

    try:
        logging.getLogger("transformers").setLevel(logging.ERROR)
        completion = ai.generate(
            n=1,
            prompt=prompt,
            do_sample=False,
            min_length=23,
            max_new_tokens=1024,
            temperature=1.00,
            # eta_cutoff=0.001,
            return_as_list=True,
            # num_beams=9,
            # num_beam_groups=3,
            top_k=10,
            penalty_alpha=0.6,
            # exponential_decay_length_penalty=(8, 1.23),
            # diversity_penalty=0.023,
            # length_penalty=1.0,
            repetition_penalty=0.88888888,
            # exponential_decay_length_penalty=(42, 1.1),
            no_repeat_ngram_size=4,
            early_stopping=True,
            renormalize_logits=True,
            max_time=360,
            seed=random.randint(0, 2**32 - 1),
        )

        output = completion[0]

    except Exception as e:
        print(e)
        output = str(e)

    active = False

    logging.getLogger("transformers").setLevel(logging.INFO)
    num = 0
    path = "/gen/mainnframe-" + str(num) + ".md"
    while os.path.exists(path):
        num = num + 1
        path = "/gen/mainnframe-" + str(num) + ".md"
    with open(path, "w") as file:
        file.write(output)
    return output


bullets = {
    "⠠",
    "⠏",
    "⠲",
    "⠢",
    "⠐",
    "⠕",
    "⠥",
    "⠭",
    "⠞",
    "⠱",
    "⠟",
    "⠒",
    "⠇",
    "⠙",
    "⠮",
    "⠪",
    "⠑",
    "⠷",
    "⠿",
    "⠊",
    "⠂",
    "⠅",
    "⠡",
    "⠬",
    "⠝",
    "⠰",
    "⠽",
    "⠻",
    "⠧",
    "⠃",
    "⠼",
    "⠹",
    "⠌",
    "⠵",
    "⠄",
    "⠎",
    "⠫",
    "⠳",
    "⠯",
    "⠗",
    "⠉",
    "⠁",
    "⠛",
    "⠸",
    "⠋",
    "⠺",
    "⠔",
    "⠓",
    "⠜",
    "⠆",
    "⠍",
    " ",
    "\n",
}
