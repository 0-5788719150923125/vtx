import functools
import asyncio
import concurrent.futures
import random
import typing
import time
import math
import os
import sys
import traceback
import re
import gc
from copy import deepcopy
import torch
from aitextgen import aitextgen
import logging
from pprint import pprint
from apscheduler.schedulers.background import BackgroundScheduler
from transformers import GenerationConfig, AutoModelForQuestionAnswering
from cerberus import Validator
from utils import (
    ad,
    bc,
    config,
    nist_beacon,
    propulsion,
    ship,
)

logging.getLogger("transformers").setLevel(logging.WARNING)

focus = os.environ["FOCUS"]


def validation(config):
    schema = {
        "info": {"type": "string"},
        "model": {"type": "string"},
        "to_gpu": {"type": "boolean"},
        "gpu_index": {"type": "integer"},
        "to_fp16": {"type": "boolean"},
        "low_memory": {"type": "boolean"},
        "max_new_tokens": {"type": "integer"},
        "petals": {"type": "boolean"},
        "focus": {"type": "dict"},
        "truncate_length": {"type": "integer"},
        "training": {
            "type": "dict",
            "schema": {
                "resume": {"type": "boolean"},
                "regen": {"type": "boolean"},
                "generate_every": {"type": "integer"},
                "save_every": {"type": "integer"},
                "gradient_checkpointing": {"type": "boolean"},
                "hivemind": {"type": "boolean"},
                "model_max_length": {"type": "integer"},
                "padding_side": {
                    "type": "string",
                    "allowed": ["left", "right"],
                },
                "peft": {
                    "type": "dict",
                    "schema": {
                        "type": {
                            "type": "string",
                            "allowed": ["lora", "prefix", "prompt"],
                        },
                        "r": {"type": "integer"},
                        "alpha": {"type": "integer"},
                        "dropout": {"type": "float"},
                        "bias": {
                            "type": "string",
                            "allowed": ["none", "lora_only", "all"],
                        },
                        "target_modules": {"type": "list"},
                        "num_virtual_tokens": {"type": "integer"},
                    },
                },
                "stages": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "learning_rate": {"type": "float"},
                            "block_size": {"type": "integer"},
                            "num_steps": {"type": "integer"},
                            "warmup_steps": {"type": "integer"},
                            "weight_decay": {"type": "float"},
                            "gradient_clip_val": {"type": "float"},
                            "scheduler": {
                                "type": "string",
                                "allowed": [
                                    "linear",
                                    "cosine",
                                    "cosine_with_restarts",
                                    "polynomial",
                                    "constant",
                                    "inverse_sqrt",
                                    "reduce_lr_on_plateau",
                                ],
                            },
                            "batch_size": {"type": "integer"},
                            "gradient_accumulation_steps": {"type": "integer"},
                            "train_transformers_only": {"type": "boolean"},
                            "equalize_datasets": {"type": "boolean"},
                            "datasets": {"type": "list"},
                        },
                    },
                },
            },
        },
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


class cortex:
    def __init__(self, config, focus):
        if not validation(config):
            raise Exception(f"Something is wrong with the {focus} configuration.")
        self.active = False
        self.ai = None
        self.focus = focus
        self.config = config
        self.context = [
            propulsion + "975174695399854150" + ship + " I am a robot.",
            propulsion + "1051994502333726841" + ship + " I am a ghost.",
            propulsion + "806051627198709760" + ship + " I am a human.",
            propulsion + "204716337971331072" + ship + " I am a medium.",
            propulsion + "855529761185857566" + ship + " I am an animal.",
        ]
        self.loader(self.focus)

    def get_max_length(self):
        return self.ai.model_max_length

    # Tokenize a string, and get its length (in tokens)
    def get_string_length(self, string):
        length = len(self.ai.tokenizer(string, return_tensors="pt")["input_ids"][0])
        return length

    # Truncate the prompt to fit the model
    def truncate_context(self, ctx, max_tokens=1024):
        length = self.get_string_length(ctx)
        while length >= max_tokens:
            ctx = ctx[5:]
            length = self.get_string_length(ctx)
        return ctx

    # Build a local cache of global conversational state
    def build_context(self, message):
        while len(self.context) >= 23:
            self.context.pop(0)

        self.context.append(message)

    # Decorator to a blocking function into a background thread
    def to_thread(func: typing.Callable) -> typing.Coroutine:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper

    def loader(self, focus):
        while self.active == True:
            time.sleep(1)

        self.active = True
        self.ai = None

        try:
            torch.cuda.empty_cache()
        except Exception as e:
            logging.error(e)

        gc.collect()

        model_folder = None
        adapter = None
        tuning_mode = None
        if "training" in self.config:
            model_folder = "models/" + focus
            if "peft" in self.config["training"]:
                model_folder = None
                t = self.config["training"]["peft"]["type"]
                if t == "lora":
                    adapter = "adapters/" + focus
                elif t == "prompt":
                    tuning_mode = "ptune"
                elif t == "prefix":
                    tuning_mode == "deep_ptune"

        try:
            print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + "focused on the " + focus)
            self.ai = aitextgen(
                model=self.config.get("model", None),
                model_folder=model_folder,
                petals=self.config.get("petals", False),
                to_gpu=self.config.get("to_gpu", False),
                cache_dir="models",
                tuning_mode=tuning_mode,
                embeddings_dir="/src/embeddings/" + focus,
                adapter=adapter,
                to_fp16=self.config.get("to_fp16", False),
            )

            if "rwkv" in getattr(self.ai.model.config, "_name_or_path"):
                print("Hacking the RWKV config...")
                self.ai.model.train()

            print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + self.config["info"])
            print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + str(self.ai))
            self.active = False
        except Exception as e:
            logging.error(e)
            time.sleep(5)
            self.active = False
            self.loader(self.focus)
            return

    @to_thread
    def chat(
        self,
        prefix=None,
        ctx=None,
        bias=None,
        max_new_tokens: int = 222,
        decay_after_length: int = 33,
        decay_factor: float = 0.00023,
    ):
        while self.active == True or not self.ai:
            time.sleep(1)

        self.active = True

        if not prefix:
            prefix = self.config.get(
                "prefix", "Humans, AI, and daemons have a conversation together:"
            )

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        eos = self.ai.tokenizer(propulsion, add_special_tokens=False).input_ids[0]
        bad = [
            self.ai.tokenizer(token, add_special_tokens=False).input_ids
            for token in ["<@", "((", "((("]
        ]

        context = self.context
        if ctx:
            context = deepcopy(ctx)

        context.insert(0, prefix)

        history = (
            self.truncate_context(
                "\n".join(context),
                self.config.get(
                    "truncate_length", math.floor(self.ai.model_max_length * 0.8)
                ),
            )
            + "\n"
        )

        prompt = history + propulsion
        if bias:
            assert len(str(bias)) in [
                18,
                19,
            ], f"The given bias ({str(bias)}) is of the wrong length."
            prompt += str(bias) + ship

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                temperature = 1.23

                if attempt > 0:
                    temperature = temperature * 0.8

                attempt += 1
                seed = nist_beacon()

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.ai.generate(
                    prompt=prompt,
                    n=1,
                    do_sample=True,
                    min_length=23,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=2.3,
                    encoder_repetition_penalty=0.999,
                    exponential_decay_length_penalty=(decay_after_length, decay_factor),
                    no_repeat_ngram_size=9,
                    low_memory=self.config.get("low_memory", False),
                    max_time=360,
                    seed=seed[1],
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    return_as_list=True,
                    eos_token_id=eos,
                    pad_token_id=getattr(self.ai.tokenizer, "pad_token_id", eos),
                    bad_words_ids=bad,
                )

                # This doesn't work very well. There are instances where the tokenizer
                # cannot perfectly replicate the input, causing a mismatch between the
                # completion and the previous history.
                generation = completion[0].replace(history, "")
                mentions = "(?:[<][@])(\d+\s*\d*)"
                variables = "(?:\({3})(\d+\s*\d*)(?:\){3})"
                group = re.search(r"^(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
                if (
                    group is None
                    or group[0] is None
                    or group[2] is None
                    or group[3] is None
                    or seed[0] is None
                    or bool(re.search(mentions, group[3]))
                    or bool(re.search(variables, group[3]))
                    or group[3] == ""
                    or propulsion in group[3]
                    or group[3][:1] in [">", "~", '"', " ", "\\", "\n", ""]
                    or group[3].endswith("\n")
                    or group[3] in prompt
                    or group[3].startswith(" ")
                ):
                    output = [False, context]
                    if attempt == max_attempts:
                        raise Exception(generation)
                    continue
                output = [group[2], group[3].replace(r"\n", "\n"), seed[0], context]
                break

            except Exception as e:
                logging.error(e)
                # print(traceback.format_exc())

        self.active = False
        return output

    @to_thread
    def prompt(
        self,
        prompt="",
        max_new_tokens: int = 111,
        decay_after_length: int = 99,
        decay_factor: float = 0.000023,
    ):
        eos = self.ai.tokenizer.convert_tokens_to_ids(
            self.ai.tokenizer.tokenize(propulsion)[0]
        )

        while self.active == True or not self.ai:
            time.sleep(1)

        self.active = True

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        bad = [
            self.ai.tokenizer(token, add_special_tokens=False).input_ids
            for token in ["{{<"]
        ]

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                temperature = 1.23
                seed = nist_beacon()

                if attempt > 0:
                    decay_factor = decay_factor / 2
                    temperature = temperature / 2

                attempt += 1

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.ai.generate(
                    prompt=prompt,
                    n=1,
                    do_sample=True,
                    min_length=23,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=1.95,
                    encoder_repetition_penalty=0.999,
                    exponential_decay_length_penalty=(decay_after_length, decay_factor),
                    no_repeat_ngram_size=9,
                    low_memory=self.config.get("low_memory", False),
                    max_time=360,
                    seed=seed[1],
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    return_as_list=True,
                    eos_token_id=eos,
                    bad_words_ids=bad,
                )

                if completion:
                    output = completion[0].replace(r"\n", "\n")
                    if output.endswith(propulsion):
                        output = output[:-1]
                    break

                output = [False, prompt]
                if attempt == max_attempts:
                    raise Exception(f"FAILED PROMPT: {prompt}")
                continue

            except Exception as e:
                logging.error(e)
                output = [False, e]

        self.active = False
        return output

    @to_thread
    def query(
        self,
        question="",
        max_new_tokens: int = 111,
        decay_after_length: int = 23,
        decay_factor: float = 0.000023,
    ):
        """
        Not functioning. This will require loading the model into QuestionAnswering
        mode, as well as attaching appropriate adapters.
        """

        while self.active == True or not self.ai:
            time.sleep(1)

        self.active = True
        # print(self.ai.model.config.supports_mode("question_answering"))
        # self.ai.model.config.model_type = "question_answering"
        self.ai.model = AutoModelForQuestionAnswering(self.ai.model)

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                temperature = 1.23
                seed = nist_beacon()

                if attempt > 0:
                    decay_factor = decay_factor / 2
                    temperature = temperature / 2

                attempt += 1

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.ai.generate(
                    prompt=question,
                    n=1,
                    do_sample=True,
                    min_length=23,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=1.95,
                    encoder_repetition_penalty=0.999,
                    exponential_decay_length_penalty=(decay_after_length, decay_factor),
                    no_repeat_ngram_size=7,
                    low_memory=self.config.get("low_memory", False),
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    max_time=360,
                    seed=seed[1],
                    return_as_list=True,
                )
                print(completion)

                output = completion[0]
                break

            except Exception as e:
                logging.error(e)
                output = [False, e]

        self.ai.model.config.model_type = "causal_lm"
        self.active = False
        return output


# Load the model and schedule periodic reloading
ctx = cortex(config[focus], focus)
# scheduler = BackgroundScheduler()
# scheduler.add_job(
#     cortex,
#     args=(
#         config[focus],
#         focus,
#     ),
#     trigger="interval",
#     minutes=30,
# )
# scheduler.start()
