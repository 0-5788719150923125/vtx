from aitextgen import aitextgen
from torch import torch
import os
import sys
import re
import time
import random
import requests

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_CACHE"] = "/tmp"

focus = os.environ["FOCUS"]
model_folder = "vtx/models/" + focus
tokenizer_file = "tokens.json"

response = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=6&type=uint8")
bullet = response.json()


def load_model():

    print(
        "INFO: Reloaded model "
        + str(bullet["data"][0])
        + " "
        + str(bullet["data"][1])
        + "."
    )

    # check quantum state
    if bullet["data"][0] < 56:
        focus = "eye"
        model_folder = "vtx/models/" + focus
    else:
        focus = os.environ["FOCUS"]
        model_folder = "vtx/models/" + focus

    # load the AI model from environment
    print("loading the " + focus)
    if focus == "eye":
        print("never fine-tune the eye")
        ai = aitextgen(model="distilgpt2", tokenizer_file=tokenizer_file, to_gpu=False)
    elif focus == "heart":
        print("never focus on the heart")
        ai = aitextgen(
            model_folder=model_folder, tokenizer_file=tokenizer_file, to_gpu=False
        )
    elif focus == "head":
        print("use your heads")
        ai = aitextgen(
            model_folder=model_folder,
            tokenizer_file=tokenizer_file,
            to_gpu=False,
        )

    return ai


# load a global model
ai = load_model()


# ping pang pong
context = [
    "975174695399854150: I am a robot.",
    "1051994502333726841: I am a ghost.",
    "204716337971331072: I am a human.",
]


def add_context(message):
    if len(context) >= 5:
        context.pop(0)
        add_context(message)
    else:
        context.append(message)


async def gen(bias):

    engine = ":"
    truncate_char = "<|endoftext|>"
    ship = ":>"
    coin = random.randrange(-1, 2, 1)
    history = "\n".join(context) + "\n"
    context.sort(reverse=False)

    # XOR Gate
    if coin > 0:
        context.sort(reverse=True)
    print(bcolors.OKGREEN + "heads" + bcolors.ENDC)

    # self-attention
    print(bcolors.FAIL + str(bias) + bcolors.ENDC)
    if (len(str(bias)) == 18) or (len(str(bias)) == 19):
        print(str(coin) + " bias toward " + str(bias))
        prompt = str(bias) + engine + " I"
    else:
        weight = str(random.randrange(99, 999, 1))
        seed = "00000"
        prompt = str(bias) + seed + str(weight)[::-1]
        print("bias toward " + str(bias) + ", weight " + str(weight))

    print(bcolors.OKGREEN + "prompt" + bcolors.ENDC)
    print(prompt[:88] + "...")
    print(bcolors.OKGREEN + "loading history" + bcolors.ENDC)

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(truncate_char)[0])
    print(history + prompt)

    # try to complete the conversation
    try:
        completion = ai.generate(
            n=2,
            prompt=history + prompt,
            do_sample=True,
            min_length=23,
            max_length=256,
            temperature=0.888,
            top_k=40,
            top_p=0.9,
            eos_token_id=eos,
            return_as_list=True,
            num_beams=3,
            repetition_penalty=2.8,
            length_penalty=1.8,
            no_repeat_ngram_size=2,
            early_stopping=False,
        )
    except Exception as e:
        print(e)
        completion = ["ERROR: The prompt does not fit the current model."]

    # generate the first completion
    print(bcolors.OKGREEN + "generation 0" + bcolors.ENDC)
    generation_zero = ""
    try:
        generation_zero = re.sub(history + prompt, prompt, completion[0])
        print(generation_zero + "...")
    except:
        print(bcolors.FAIL + "history mismatch" + bcolors.ENDC)

    print(bcolors.OKGREEN + "truncated" + bcolors.ENDC)

    # attempt to generate other completions
    print(bcolors.OKGREEN + "generation 1" + bcolors.OKGREEN)
    generation_one = ""
    try:
        generation_one = re.search(
            r"^(.*)(\d{18,19})(?::\s*)(.*)(?:\n*)", generation_zero
        )
        print(generation_one[0][:99] + "...")
        generation_one = generation_one[0] + ": " + generation_one[1]
        print(generation_one[0] + "...")
    except:
        generation_one = generation_zero

    print(generation_one[:33] + "...")

    attention = [1]

    # focus attention
    print(bcolors.OKGREEN + "attention" + bcolors.OKGREEN)
    try:
        attention[0] = re.search(r"^(.*)(\d{18,19})(?::\s*)(.*)(?:\n*)", generation_one)
        print("=> " + attention[0][:33] + "...")
        print("=> " + attention[2][:111] + "...")
    except:
        attention[0] = generation_one

    try:
        print(bcolors.OKGREEN + "focus" + bcolors.ENDC)
        attn = re.search(r"^(.*)(\d{18,19})(?::\s*)(.*)(?:\n*)", attention[0])
        print(focus)
        print(bcolors.WARNING + "point" + bcolors.ENDC)
        point = attn[2] + ": " + attn[3]
        print(point)

        print(bcolors.WARNING + "transformer" + bcolors.ENDC)
        data = re.search(r"^(.*)(\d{18,19})(?::\s*)(.*)(?:\n*)", point)
        output = transformer([data[2], data[3]])
        print(bcolors.OKCYAN + "completion" + bcolors.ENDC)
    except:
        output = completion[0]
    print(bcolors.OKGREEN + "=> " + output[:888] + "..." + bcolors.ENDC)
    return output


# universal key
def transformer(group):
    print(group)
    responses = [
        f'The ghost of <@{group[0]}> suggests, *"{group[1]}"*',
        f'<@{group[0]}> says, *"{group[1]}"*',
        f'<@{group[0]}> would say, *"{group[1]}"*',
        f'They said, *"{group[1]}"*',
        f"{group[1]}",
        ".",
    ]
    string = random.choice(responses)
    return string


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
