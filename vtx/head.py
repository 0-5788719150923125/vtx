import functools
import asyncio
import random
import typing
import shutil
import time
import os
import sys
import signal
import re
import gc
import torch
import time
from utils import ad, bc, config, get_quantum_seed, propulsion, ship
from aitextgen import aitextgen
import requests
import logging
from transformers import AutoTokenizer, GenerationConfig

# holds the model globally
ai = None
active = False

os.environ["LRU_CACHE_CAPACITY"] = "1"
cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path
# os.environ["CUDA_LAUNCH_BLOCKING"] = "1"
# os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

focus = os.environ["FOCUS"]

# when all fails, reset to this context
default_context = [
    propulsion + "975174695399854150" + ship + " I am a robot.",
    propulsion + "1051994502333726841" + ship + " I am a ghost.",
    propulsion + "806051627198709760" + ship + " I am a human.",
    propulsion + "204716337971331072" + ship + " I am a medium.",
    propulsion + "855529761185857566" + ship + " I am an animal.",
]

context = default_context.copy()


# Decorator to a blocking function into a background thread
def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


# Load the specified model
@to_thread
def loader(target=None):
    global active

    while active == True:
        time.sleep(1)

    active = True
    try:
        global ai
        ai = None
        torch.cuda.empty_cache()
        gc.collect()
    except Exception as e:
        print(e)

    if target == None:
        target = focus

    model = config[target]

    if "training" in model:
        model_folder = "models/" + target
        base = model["training"].get("base_model", None)
    else:
        model_folder = None
        base = model.get("model", None)

    try:
        print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + "focused on the " + target)
        logging.getLogger("transformers").setLevel(logging.ERROR)
        ai = aitextgen(
            model=model.get("model", None),
            model_folder=model_folder,
            tokenizer_file=None,
            to_gpu=model["to_gpu"],
            cache_dir="models",
        )
        ai.tokenizer = AutoTokenizer.from_pretrained(
            base,
            cache_dir="models",
            padding_side="left",
        )
        logging.getLogger("transformers").setLevel(logging.INFO)
        print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + model["info"])
        print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + str(ai))
    except Exception as e:
        print(e)
        time.sleep(15)
        ai = asyncio.run(loader(target))
    active = False
    return ai


# Build a local cache of global conversational state
def build_context(message):
    while len(context) >= 23:
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


# Generate a completion from bias and context
@to_thread
def gen(
    bias=None,
    ctx=None,
    prefix: str = "Humans, AI, and daemons have a conversation together:",
    max_new_tokens: int = config[focus].get("max_new_tokens", 111),
    decay_after_length: int = 59,
):
    global ai
    global active

    while active == True:
        time.sleep(1)

    active = True

    prompt = propulsion

    if ctx == None:
        global context
        ctx = context

    ctx = truncate_context(ctx, config[focus].get("context_length", 1024))
    history = prefix + "\n" + "\n".join(ctx) + "\n"

    # bias the prompt
    if bias is not None:
        if (len(str(bias)) == 18) or (len(str(bias)) == 19):
            prompt = propulsion + str(bias) + ship

    # verify 50% of seeds
    verified = random.choice([True, False])
    seed = [False, random.randint(0, 2**32 - 1)]
    if verified:
        seed = get_quantum_seed()
        if not seed[0]:
            verified = False

    torch.cuda.empty_cache()

    attempt = 1
    max_attempts = 9
    while attempt <= max_attempts:
        try:
            output = None

            eos = ai.tokenizer.convert_tokens_to_ids(
                ai.tokenizer.tokenize(propulsion)[0]
            )

            temperature = 1.23
            if attempt > 0:
                temperature = temperature - (0.1 * attempt)

            # try to complete the prompt
            # https://huggingface.co/docs/transformers/main_classes/text_generation
            params = GenerationConfig(
                n=1,
                do_sample=True,
                min_length=23,
                max_length=10000,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                eta_cutoff=0.0003,
                penalty_alpha=0.6,
                top_k=4,
                repetition_penalty=1.89,
                encoder_repetition_penalty=0.4,
                exponential_decay_length_penalty=(decay_after_length, 1.21),
                # no_repeat_ngram_size=9,
                renormalize_logits=True,
                remove_invalid_values=True,
                eos_token_id=eos,
                max_time=60,
                seed=seed[1],
            )

            completion = ai.generate(
                prompt=history + prompt,
                generation_config=params,
                return_as_list=True,
            )

            active = False
            generation = completion[0][len(history) :]
            mentions = "(?:[<][@])(\d+\s*\d*)"
            variables = "(?:\({3})(\d+\s*\d*)(?:\){3})"
            group = re.search(r"^(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
            if (
                group is None
                or propulsion in group[3]
                or bool(re.search(mentions, group[3]))
                or bool(re.search(variables, group[3]))
            ):
                raise Exception("failed to format a proper response")
            else:
                output = [group[2], group[3], verified]
                break

        except Exception as e:
            attempt = attempt + 1
            if attempt > max_attempts:
                if str(e) == "failed to format a proper response":
                    context = default_context.copy()
                    output = ["error", "ERROR: Me Found.", False]
                else:
                    torch.cuda.empty_cache()
                    command = [sys.executable] + sys.argv
                    os.execv(sys.executable, command)

    active = False
    return output


# Generate a completion from bias and context
@to_thread
def predict(
    prompt: str = """A push...""",
    max_new_tokens: int = 1024,
    decay_after_length: int = 512,
):
    global active

    while active == True:
        time.sleep(1)

    active = True

    try:
        logging.getLogger("transformers").setLevel(logging.ERROR)
        completion = ai.generate(
            n=1,
            prompt=prompt,
            do_sample=True,
            min_length=23,
            max_new_tokens=max_new_tokens,
            temperature=1.23,
            eta_cutoff=0.0003,
            return_as_list=True,
            top_k=5,
            penalty_alpha=0.666,
            repetition_penalty=1.59,
            encoder_repetition_penalty=1.023,
            exponential_decay_length_penalty=(decay_after_length, 1.059),
            no_repeat_ngram_size=4,
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

    if not os.path.exists("/gen/generations"):
        os.makedirs("/gen/generations")

    num = 0
    path = "/gen/generations/test-" + str(num) + ".md"

    while os.path.exists(path):
        num = num + 1
        path = "/gen/generations/test-" + str(num) + ".md"
    with open(path, "w") as file:
        file.write(output)
    return output
