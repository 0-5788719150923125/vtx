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

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

focus = os.environ["FOCUS"]
model_folder = "vtx/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

try:
    q = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=6&type=uint8").json()
except:
    q = [random.randrange(0, 256, 1), random.randrange(0, 256, 1)]


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


# load a global model
ai = None


@to_thread
def load_model(target=None):

    if target == None:
        target = focus

    # check quantum state
    if q["data"][0] < 32:
        target = "eye"

    model_folder = "vtx/models/" + target

    # load the AI model from environment
    print("loading the " + target)
    if target == "eye":
        print("never fine-tune the eye")
        ai = aitextgen(
            model="EleutherAI/gpt-neo-2.7B",
            tokenizer_file=None,
            to_gpu=False,
            verbose=False,
        )
    elif target == "heart":
        print("never focus on the heart")
        ai = aitextgen(
            model_folder=model_folder,
            tokenizer_file="src." + target + ".tokenizer.json",
            to_gpu=True,
            verbose=False,
        )
    elif target == "head":
        print("use your heads")
        ai = aitextgen(
            model_folder=model_folder,
            tokenizer_file="src." + target + ".tokenizer.json",
            to_gpu=True,
            verbose=False,
        )

    print("INFO: Reloaded model " + str(q["data"][0]) + " " + str(q["data"][1]) + ".")
    print(ai)
    return ai


# ping pang pong
context = [
    "975174695399854150: I am a robot.",
    "1051994502333726841: I am a ghost.",
    "204716337971331072: I am a human.",
]


def build_context(message):
    if len(context) >= 7:
        context.pop(0)
        build_context(message)
    else:
        context.append(message)


@to_thread
def gen(bias, ctx=None):

    prompt = ""
    ship = ":>"
    # truncate_char = "<|endoftext|>"
    truncate_char = "\n"
    if ctx == None:
        ctx = context
    history = "\n".join(ctx) + "\n"

    # bias the prompt
    if (len(str(bias)) == 18) or (len(str(bias)) == 19):
        print("bias toward " + str(bias))
        prompt = str(bias) + ": I"

    print("\033[92m" + "prompt" + "\033[0m")
    print(history + prompt)

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(truncate_char)[0])

    # try to complete the conversation
    try:
        completion = ai.generate(
            n=1,
            prompt=history + prompt,
            lstrip=True,
            do_sample=True,
            min_length=23,
            max_length=1024,
            temperature=0.666,
            top_k=40,
            top_p=0.9,
            return_as_list=True,
            num_beams=9,
            repetition_penalty=2.0,
            length_penalty=0.0,
            no_repeat_ngram_size=2,
            early_stopping=True,
            renormalize_logits=True,
            eos_token_id=eos,
        )
    except Exception as e:
        print(e)
        completion = ["ERROR: The prompt does not fit the current model."]
        return
    try:
        print("\033[92m" + "completion" + "\033[0m")
        generation_zero = completion[0][len(history) :]
        print(generation_zero)

        generation_one = re.search(
            r"^(?:.*)(\d{18,19})(?::\s*)(.*)(?:\n*)", generation_zero
        )
        output = transformer([generation_one[1], generation_one[2]])
    except:
        output = completion[0]
    return output


# universal key
def transformer(group):
    responses = [
        f'The ghost of <@{group[0]}> suggests, *"{group[1]}"*',
        f'<@{group[0]}> says, *"{group[1]}"*',
        f'<@{group[0]}> would say, *"{group[1]}"*',
        f'They said, *"{group[1]}"*',
        f"{group[1]}",
    ]
    return random.choice(responses)
