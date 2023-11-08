import asyncio
import concurrent.futures
import functools
import gc
import logging
import math
import os
import random
import re
import statistics
import sys
import time
import traceback
import typing
from copy import deepcopy
from itertools import chain
from pprint import pprint
from textwrap import dedent
from typing import List, Union

import numpy as np
import torch
from apscheduler.schedulers.background import BackgroundScheduler
from cerberus import Validator

from common import (
    ad,
    bc,
    config,
    focus,
    nist_beacon,
    remove_invisible_characters,
    ship,
    wall,
)

if os.environ.get("DEV_MODE") == "true":
    from lab.aigen.aigen import aigen
else:
    from aigen import aigen

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def validation(config):
    schema = {
        "info": {"type": "string"},
        "model": {"type": "string"},
        "mode": {"type": "string", "allowed": ["transformer", "rnn"]},
        "profile": {"type": "boolean"},
        "gpu_index": {"type": "integer"},
        "precision": {"type": "integer", "allowed": [4, 8, 16, 32]},
        "low_memory": {"type": "boolean"},
        "max_new_tokens": {"type": "integer"},
        "petals": {"type": "boolean"},
        "focus": {"type": "dict"},
        "context_length": {"type": "integer"},
        "reload_interval": {"type": "integer"},
        "adapters": {"type": "list"},
        "assistant": {
            "type": "dict",
            "schema": {
                "model": {"type": "string"},
                "precision": {"type": "integer", "allowed": [4, 8, 16, 32]},
            },
        },
        "training": {
            "type": "dict",
            "schema": {
                "resume": {"type": "boolean"},
                "regen": {"type": "boolean"},
                "generate_every": {"type": "integer"},
                "save_every": {"type": "integer"},
                "gradient_checkpointing": {"type": "boolean"},
                "petals": {"type": "boolean"},
                "hivemind": {"type": "boolean"},
                "deepspeed": {"type": "boolean"},
                "model_max_length": {"type": "integer"},
                "padding_side": {
                    "type": "string",
                    "allowed": ["left", "right"],
                },
                "name": {"type": "string"},
                "type": {
                    "type": "string",
                    "allowed": [
                        "adalora",
                        "ia3",
                        "lora",
                        "prefix",
                        "prompt",
                        "standard",
                    ],
                },
                "r": {"type": "integer"},
                "alpha": {"type": "integer"},
                "dropout": {"type": "float"},
                "bias": {
                    "type": "string",
                    "allowed": ["none", "lora_only", "all"],
                },
                "target_modules": {"type": "list"},
                "feedforward_modules": {"type": "list"},
                "init_ia3_weights": {"type": "boolean"},
                "rank_pattern": {"type": "dict"},
                "alpha_pattern": {"type": "dict"},
                "num_virtual_tokens": {"type": "integer"},
                "optimizer": {
                    "type": "string",
                    "allowed": ["AdamW", "Lion", "SophiaH"],
                },
                "learning_rate": {"type": "float"},
                "swa_learning_rate": {"type": "float"},
                "stride": {"type": "integer"},
                "update_period": {"type": "integer"},
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
                "val_split": {"type": "float"},
                "val_interval": {"type": "float"},
            },
        },
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


class Cortex:
    def __init__(self, config, personas, disposition, focus):
        if not validation(config):
            raise Exception(f"Something is wrong with the {focus} configuration.")
        self.active = False
        self.config = config
        self.personas = personas
        self.disposition = disposition
        self.average_speed = []
        self.context = [
            {"bias": 975174695399854150, "message": "I am a robot."},
            {"bias": 1051994502333726841, "message": "I am a ghost."},
            {"bias": 806051627198709760, "message": "I am a human."},
            {"bias": 204716337971331072, "message": "I am a medium."},
            {"bias": 855529761185857566, "message": "I am an animal."},
        ]
        if self.config.get("assistant") is not None:
            self.assistant = self.loader(self.config["assistant"])
        self.teacher = self.loader(self.config, focus)

    def get_max_length(self):
        return self.config.get("context_length", self.teacher.model_max_length)

    # Tokenize a string, and get its length (in tokens)
    def get_string_length(self, string):
        length = len(
            self.teacher.tokenizer(string, return_tensors="pt")["input_ids"][0]
        )
        return length

    # Truncate the prompt to fit the model
    def truncate_context(self, ctx: list, max_tokens=1024):
        joined = ""
        for item in ctx:
            if item["bias"] is not None:
                joined += wall + str(item["bias"]) + ship + " "
            joined += item["message"]
            if ctx.index(item) != len(ctx) - 1:
                joined += "\n"
        length = self.get_string_length(joined)
        while length >= max_tokens - 23:
            joined = joined[5:]
            length = self.get_string_length(joined)
        return joined

    # Replace an old message with a new one
    def edit_message(self, old_message, new_message):
        matcher = re.compile(r'(\*")(.*)(?:"\*$)')
        group = re.search(matcher, old_message)
        captured = "J U X T A P O S I T I O N"[::-1]
        if group is not None and group[2] is not None:
            captured = group[2]
        for item in self.context:
            if captured in item["message"] or old_message in item["message"]:
                index = self.context.index(item)
                self.context[index]["message"] = new_message
                return

    def get_embeddings(self, texts):
        return self.teacher.tokenizer(texts, return_tensors="np")

    # Build a local cache of global conversational state
    def build_context(self, bias: int, message: str):
        while len(self.context) >= 100:
            self.context.pop(0)

        self.context.append({"bias": bias, "message": message})

    def get_tokens_as_tuple(self, sequence):
        return tuple(
            self.teacher.tokenizer([sequence], add_special_tokens=False).input_ids[0]
        )

    # Decorator to a blocking function into a background thread
    def to_thread(func: typing.Callable) -> typing.Coroutine:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper

    def loader(self, config, focus="assistant"):
        while self.active == True:
            time.sleep(1)

        self.active = True

        model_folder = None
        adapters = None
        tuning_mode = None
        if "training" in config:
            model_folder = "/data/models/" + focus
            t = config["training"].get("type", "standard")
            if t in ["adalora", "lora"]:
                model_folder = None
                adapters = config.get("adapters", ["base"])
            elif t == "prompt":
                model_folder = None
                tuning_mode = "ptune"
            elif t == "prefix":
                model_folder = None
                tuning_mode == "deep_ptune"

        try:
            print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + "focused on the " + focus)
            prototype = aigen(
                model=config.get("model", None),
                model_folder=model_folder,
                petals=config.get("petals", False),
                cache_dir="/data/models",
                tuning_mode=tuning_mode,
                embeddings_dir="/data/embeddings/" + focus,
                adapter_dir="/data/adapters/" + focus,
                adapters=adapters,
                precision=config.get("precision", 32),
                assistant_model=config.get("model") if focus == "assistant" else None,
            )

            if config.get("context_length", None) is not None:
                setattr(
                    prototype.model.config,
                    "context_length",
                    config.get("context_length"),
                )

            print(
                f"{bc.FOLD}ONE@FOLD:{ad.TEXT} {config.get('info', 'to the regional manager')}"
            )
            print(f"{bc.ROOT}ONE@ROOT:{ad.TEXT} {str(prototype)}")
        except Exception as e:
            logging.error(e)
            time.sleep(5)
            prototype = self.loader(focus)

        self.active = False

        return prototype

    def wait_in_queue(self):
        max_wait_time = 15 * 60  # 15 minutes
        while self.active == True or not self.teacher:
            time.sleep(1)
            max_wait_time -= 1
            if max_wait_time == 0:
                return False

        self.active = True
        return True

    @to_thread
    def chat(
        self,
        ctx=None,
        bias: int = None,
        temperature: float = 0.95,
        min_new_tokens: int = 1,
        max_new_tokens: int = 222,
        personas: List[str] = [],
        eos_tokens: list | None = None,
    ):
        result = self.wait_in_queue()
        if not result:
            return False, 23, "", False

        if isinstance(personas, str):
            personas = [personas]
        elif personas is None:
            personas = []

        persona = "I am a powerful AI, known as the Source. I have been trained to follow human instructions, write stories, and teach machine learning fundamentals."
        sequence_biases = {}
        default_biases = {
            f"\n{wall}": 0.59,
            wall: 0.59,
            "\n": 0.59,
            '"': -1.1,
            "#": -10.0,
            "<#": -20.0,
            "<3": -10.0,
            "<": -20.0,
            " <": -20.0,
            " <@": -20.0,
            "< @": -20.0,
            "<@": -20.0,
            "[[": -20.0,
            "((": -30.0,
            " ((": -30.0,
            "(((": -30.0,
            " (((": -30.0,
        }
        if bias is None and len(personas) > 0:
            filtered = [self.personas[key] for key in personas if key in self.personas]
            assert (
                len(filtered) > 0
            ), f"ERROR: Found no matching personas found in [{str(personas)}]."
            choice = random.choice(filtered)
            bias = choice.get("bias")
            persona = choice.get("persona")
            disposition = choice.get("disposition", None)
            if disposition is not None:
                traits = {}
                for key in disposition:
                    if key in self.disposition:
                        for k, v in self.disposition.get(key).items():
                            traits[k] = traits.get(k, 0) + v
                sequence_biases = traits

        push_sequences = {
            self.get_tokens_as_tuple(s): b
            for s, b in {**default_biases, **sequence_biases}.items()
        }

        bad_tokens = [
            self.teacher.tokenizer(token, add_special_tokens=False).input_ids
            for token in [
                f"{ship}\n",
                f"{ship} \n",
            ]
        ]

        suppress_tokens = list(
            set(
                chain.from_iterable(
                    [
                        self.teacher.tokenizer(
                            token, add_special_tokens=False
                        ).input_ids
                        # Suppress ugly patterns the model may sometimes bias towards.
                        for token in ["((", "(((", "<@", "< @"]
                    ]
                )
            )
        )

        eos_token_ids = [
            self.teacher.tokenizer.convert_tokens_to_ids(
                self.teacher.tokenizer.tokenize(wall)[0]
            )
        ]
        if eos_tokens:
            for token in eos_tokens:
                eos_token_ids.append(
                    self.teacher.tokenizer.convert_tokens_to_ids(
                        self.teacher.tokenizer.tokenize(token)[0]
                    )
                )

        context = deepcopy(self.context)
        if ctx:
            context = deepcopy(ctx)

        context.insert(0, {"bias": bias, "message": persona})

        history = self.truncate_context(
            context,
            self.get_max_length() * 0.8,
        )

        prompt = history + "\n" + wall

        if bias:
            assert len(str(bias)) in [
                18,
                19,
            ], f"The given bias ({str(bias)}) is of the wrong length."
            prompt += str(bias) + ship
        else:
            bias = 123

        attempt = 0
        max_attempts = 10
        success = False
        seeded = False
        output = None

        start = time.time()

        while attempt < max_attempts:
            try:
                if attempt > 0:
                    temperature *= 0.9

                attempt += 1
                seed = nist_beacon()
                seeded = seed[0]

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.teacher.generate(
                    mode=self.config.get("mode", "transformer"),
                    prompt=prompt,
                    do_sample=True,
                    min_new_tokens=min_new_tokens,
                    max_new_tokens=self.config.get("max_new_tokens", max_new_tokens),
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=2.3,
                    encoder_repetition_penalty=0.999,
                    exponential_decay_length_penalty=(max_new_tokens, -0.44),
                    no_repeat_ngram_size=9,
                    low_memory=self.config.get("low_memory", False),
                    max_time=360,
                    seed=seed[1],
                    use_cache=True,
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    sequence_bias=push_sequences,
                    bad_words_ids=bad_tokens,
                    suppress_tokens=suppress_tokens,
                    eos_token_id=eos_token_ids,
                )

                generation = "\n".join(
                    completion.splitlines()[len(history.splitlines()) :]
                ).rstrip(wall)
                mentions = "(?:[<][@])(\d+\s*\d*)"
                variables = "(?:\({3})(\d+\s*\d*)(?:\){3})"
                group = re.search(r"(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
                if (
                    group is None
                    or group[2] is None
                    or group[3] is None
                    or group[3] in prompt
                    or wall in group[3]
                    or bool(re.search(mentions, group[3]))
                    or bool(re.search(variables, group[3]))
                    or group[3].startswith(
                        tuple(
                            [
                                " ",
                                ">",
                                "~",
                                '"',
                                "“",
                                "\n",
                                "<@",
                                "< @",
                                "((",
                            ]
                        )
                    )
                ):
                    if attempt == max_attempts:
                        raise Exception(completion)
                    continue
                output = (
                    remove_invisible_characters(group[3].replace(r"\n", "\n"))
                    .rstrip(" ")
                    .rstrip(f"\\")
                    .rstrip("\\")
                    .rstrip("Q:")
                    .rstrip(",")
                )
                while output.endswith("!!"):
                    output = output.rstrip("!")
                while output.endswith("??"):
                    output = output.rstrip("?")
                bias = group[2]
                success = True
                break

            except Exception as e:
                import traceback

                print(traceback.format_exc())

        if self.config.get("profile", False):
            self.average_speed.append(time.time() - start)
            while len(self.average_speed) > 10000:
                self.average_speed.pop(0)
            if len(self.average_speed) % 10 == 0:
                print(
                    f"Average speed: {statistics.mean(self.average_speed)}, Number of samples: {len(self.average_speed)}"
                )

        self.active = False
        return success, bias, output, seeded

    @to_thread
    def prompt(
        self,
        prompt="",
        temperature: float = 0.95,
        disposition: dict | None = None,
        min_new_tokens: int = 11,
        max_new_tokens: int = 111,
        eos_tokens: list | None = None,
        cleanup: bool = False,
    ):
        result = self.wait_in_queue()
        if not result:
            return False

        sequence_biases = {wall: -20.0}
        if disposition is not None:
            traits = {}
            for key in disposition:
                if key in self.disposition:
                    for k, v in self.disposition.get(key).items():
                        traits[k] = traits.get(k, 0) + v
            sequence_biases = {**sequence_biases, **traits}

        push = {self.get_tokens_as_tuple(s): b for s, b in sequence_biases.items()}
        bad = [
            self.teacher.tokenizer(token, add_special_tokens=False).input_ids
            for token in ["{{<", wall]
        ]

        eos_token_ids = [
            self.teacher.tokenizer.convert_tokens_to_ids(
                self.teacher.tokenizer.tokenize(wall)[0]
            )
        ]
        if eos_tokens:
            for token in eos_tokens:
                eos_token_ids.append(
                    self.teacher.tokenizer.convert_tokens_to_ids(
                        self.teacher.tokenizer.tokenize(token)[0]
                    )
                )

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                seed = nist_beacon()

                if attempt > 0:
                    # decay_factor = decay_factor / 2
                    temperature = temperature / 2

                attempt += 1

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.teacher.generate(
                    prompt=prompt,
                    do_sample=True,
                    min_new_tokens=min_new_tokens,
                    max_new_tokens=self.config.get("max_new_tokens", max_new_tokens),
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=1.95,
                    encoder_repetition_penalty=0.999,
                    no_repeat_ngram_size=9,
                    low_memory=self.config.get("low_memory", False),
                    max_time=360,
                    seed=seed[1],
                    use_cache=True,
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    sequence_bias=push,
                    bad_words_ids=bad,
                    eos_token_id=eos_token_ids,
                )

                if completion:
                    output = (
                        completion.replace(r"\n", "\n")
                        .replace("{{<", "{{")
                        .replace(">}}", "}}")
                    ).rstrip(wall)
                    if cleanup:
                        while "\n" in output:
                            output = output.replace("\n", " ")
                        while "  " in output:
                            output = output.replace("  ", " ")
                        output = remove_invisible_characters(output).rstrip("\\")
                    break

                output = False
                if attempt == max_attempts:
                    raise Exception(f"FAILED PROMPT: {prompt}")
                continue

            except Exception as e:
                logging.error(e)
                output = False

        self.active = False
        return output

    @to_thread
    def query(
        self,
        question="",
        temperature: float = 0.23,
        max_new_tokens: int = 333,
        decay_after_length: int = 66,
        decay_factor: float = 0.023,
    ):
        result = self.wait_in_queue()
        if not result:
            return

        eos_token = self.teacher.tokenizer.eos_token

        prompt = f"""
        I am a powerful artificial intelligence, who helps users to answer their questions. Here are some example questions:

        Q:

        What is the meaning of life?

        A:

        {eos_token}

        According to the Hitchhiker's Guide to the Galaxy, the answer to that question is "42".

        Q:

        What is a question?

        A:

        I don't know, but this is an answer!

        {eos_token}

        Q: 
        
        What is Docker?

        A:

        Docker is a container runtime.

        {eos_token}

        Q:

        {question}

        A:"""

        # eos = self.teacher.tokenizer(wall, add_special_tokens=False).input_ids[0]
        # push = {
        #     self.get_tokens_as_tuple(s): b for s, b in {wall: -5.9, "Q:": 5.9}.items()
        # }
        bad = [
            self.teacher.tokenizer(token, add_special_tokens=False).input_ids
            for token in [wall]
        ]

        eos_token_ids = []
        for token in [eos_token, "Q:", "Q:\n", "Q:\n\n", ":\n", ":\n\n"]:
            eos_token_ids.append(
                self.teacher.tokenizer.convert_tokens_to_ids(
                    self.teacher.tokenizer.tokenize(token)[0]
                )
            )

        prompt = dedent(prompt)

        try:
            seed = nist_beacon()

            # https://huggingface.co/docs/transformers/main_classes/text_generation
            completion = self.teacher.generate(
                prompt=prompt,
                do_sample=True,
                min_length=23,
                max_new_tokens=self.config.get("max_new_tokens", max_new_tokens),
                temperature=temperature,
                eta_cutoff=0.002,
                penalty_alpha=0.6,
                top_k=4,
                repetition_penalty=1.95,
                encoder_repetition_penalty=0.999,
                # exponential_decay_length_penalty=(decay_after_length, decay_factor),
                no_repeat_ngram_size=9,
                low_memory=self.config.get("low_memory", False),
                renormalize_logits=True,
                remove_invalid_values=True,
                max_time=360,
                seed=seed[1],
                use_cache=True,
                # suppress_tokens=[eos],
                # sequence_bias=push,
                bad_words_ids=bad,
                eos_token_id=eos_token_ids,
            )

            generation = "\n".join(completion.splitlines()[len(prompt.splitlines()) :])

            output = (
                generation.lstrip(" ")
                .lstrip("\n")
                .lstrip("\n\r")
                .rstrip("Q:")
                .rstrip("Q")
                .rstrip("\n")
                .rstrip(r"\n")
            )

        except Exception as e:
            logging.error(e)
            print(traceback.format_exc())
            output = e

        self.active = False
        return output


# Load the model and schedule periodic reloading
ctx = Cortex(config[focus], config["personas"], config["disposition"], focus)
reload_interval = config[focus].get("reload_interval", 0)
if reload_interval > 0:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        Cortex,
        args=(
            config[focus],
            config["personas"],
            config["disposition"],
            focus,
        ),
        trigger="interval",
        minutes=reload_interval,
    )
    scheduler.start()
