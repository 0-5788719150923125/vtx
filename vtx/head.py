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
to_gpu = False
model_folder = "vtx/models/" + focus
tokenizer_file = "src." + focus + ".tokenizer.json"

try:
    q = requests.get("https://qrng.anu.edu.au/API/jsonI.php?length=6&type=uint8").json()
except:
    q = [random.randrange(0, 256, 1), random.randrange(0, 256, 1)]


def load_model():

    print("INFO: Reloaded model " + str(q["data"][0]) + " " + str(q["data"][1]) + ".")

    # check quantum state
    if q["data"][0] < 32:
        focus = "eye"
        model_folder = "vtx/models/" + focus
    else:
        focus = os.environ["FOCUS"]
        model_folder = "vtx/models/" + focus

    # load the AI model from environment
    print("loading the " + focus)
    if focus == "eye":
        print("never fine-tune the eye")
        ai = aitextgen(model="distilgpt2", tokenizer_file=tokenizer_file, to_gpu=to_gpu)
    elif focus == "heart":
        print("never focus on the heart")
        ai = aitextgen(
            model_folder=model_folder, tokenizer_file=tokenizer_file, to_gpu=to_gpu
        )
    elif focus == "head":
        print("use your heads")
        ai = aitextgen(
            model_folder=model_folder,
            tokenizer_file=tokenizer_file,
            to_gpu=to_gpu,
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


def build_context(message):
    if len(context) >= 7:
        context.pop(0)
        build_context(message)
    else:
        context.append(message)


async def gen(bias):

    ship = ":>"
    truncate_char = "<|endoftext|>"

    history = "\n".join(context) + "\n"
    print(bcolors.OKGREEN + "heads" + bcolors.ENDC)

    # self-attention
    coin = random.choice([0, 1])
    print(bcolors.FAIL + str(bias) + bcolors.ENDC)
    if (len(str(bias)) == 18) or (len(str(bias)) == 19):
        print(str(coin) + " bias toward " + str(bias))
        prompt = str(bias) + ": I"
    else:
        weight = str(random.randrange(99, 999, 1))
        currentLength = len(str(bias) + str(weight))
        seed = ""
        if currentLength != 18 and currentLength != 19:
            while currentLength < random.randrange(18, 20, 1):
                seed = seed + "0"
                currentLength = currentLength + 1
        # prompt = str(bias) + seed + str(weight)[::-1] + ": "
        prompt = ""
        print("bias toward " + str(bias) + ", weight " + str(weight))

    eos = ai.tokenizer.convert_tokens_to_ids(ai.tokenizer.tokenize(truncate_char)[0])

    print(bcolors.OKGREEN + "prompt" + bcolors.ENDC)
    print(history + prompt)

    # try to complete the conversation
    try:
        completion = ai.generate(
            n=2,
            prompt=history + prompt,
            lstrip=True,
            do_sample=True,
            min_length=23,
            max_length=512,
            temperature=0.888,
            top_k=40,
            top_p=0.9,
            # eos_token_id=eos,
            return_as_list=True,
            num_beams=3,
            # num_beam_groups=3,
            repetition_penalty=2.0,
            length_penalty=-7.0,
            no_repeat_ngram_size=2,
            early_stopping=True,
            renormalize_logits=True,
        )
    except Exception as e:
        print(e)
        completion[0] = ["ERROR: The prompt does not fit the current model."]
    try:
        print(bcolors.OKGREEN + "completion" + bcolors.ENDC)
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
