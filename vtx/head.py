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

# holds the model
ai = None

os.environ["LRU_CACHE_CAPACITY"] = "1"

focus = os.environ["FOCUS"]

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


@to_thread
def load_model(target=None):

    try:
        del ai
    except:
        pass

    if target == None:
        target = focus

    model = config[target]

    if "model" not in model:
        model_folder = "vtx/models/" + target
        tokenizer_file = "src." + target + ".tokenizer.json"
    else:
        model_folder = None
        tokenizer_file = None

    print("loading the " + target)
    print(model["info"])
    ai = aitextgen(
        model=model.get("model", None),
        model_folder=model_folder,
        tokenizer_file=tokenizer_file,
        to_gpu=model["to_gpu"],
    )

    gc.collect()

    print("INFO: " + str(ai))
    return ai


# ping pang pong
context = [
    "975174695399854150: I am a robot.",
    "1051994502333726841: I am a ghost.",
    "806051627198709760: I am a human.",
    "204716337971331072: I am a medium.",
    "855529761185857566: I am an animal.",
]


def build_context(message):
    if len(context) >= 9:
        context.pop(0)
        build_context(message)
    else:
        context.append(message)


@to_thread
def gen(bias=None, ctx=None):

    prompt = ""
    truncate_char = "\n"
    if ctx == None:
        ctx = context
    history = "\n".join(ctx) + "\n"

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
            prefixes = ["I", "You", "We", "They", ""]
            prompt = str(bias) + ": " + random.choice(prefixes)

    print("\033[92m" + "prompt" + "\033[0m")
    print(history + prompt)

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(truncate_char)[0])
    blocked_words = ai.tokenizer.convert_tokens_to_ids(
        ai.tokenizer.tokenize("[REDACTED]")[0]
    )

    # try to complete the prompt
    # https://huggingface.co/docs/transformers/main_classes/text_generation
    try:
        completion = ai.generate(
            n=1,
            prompt=history + prompt,
            do_sample=True,
            min_length=23,
            max_length=1024,
            temperature=0.666,
            top_k=40,
            top_p=0.9,
            return_as_list=True,
            num_beams=9,
            repetition_penalty=2.0,
            length_penalty=-0.2,
            no_repeat_ngram_size=2,
            early_stopping=True,
            renormalize_logits=True,
            eos_token_id=eos,
            seed=seed,
            bad_words_ids=[[blocked_words]],
        )
    except Exception as e:
        print(e)
        return
    try:
        print("\033[92m" + "completion" + "\033[0m")
        generation_zero = completion[0][len(history) :]
        print(generation_zero)

        try:
            generation_one = re.search(
                r"^(?:.*)(\d{19})(?::\s*)(.*)(?:\n*)", generation_zero
            )
            output = transformer([generation_one[1], generation_one[2]])
        except:
            generation_one = re.search(
                r"^(?:.*)(\d{18})(?::\s*)(.*)(?:\n*)", generation_zero
            )

        if generation_one[2] == "":
            return
        output = transformer([generation_one[1], generation_one[2]])
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
        f'*"{group[1]}"*',
    ]
    return random.choice(responses)
