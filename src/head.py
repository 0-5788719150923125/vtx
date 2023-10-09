import asyncio
import concurrent.futures
import functools
import gc
import logging
import math
import os
import random
import re
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

mode = os.environ.get("DEV_MODE", None)
if mode == "true":
    from lab.aigen.aigen import aigen
else:
    from aigen import aigen

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


def validation(config):
    schema = {
        "info": {"type": "string"},
        "model": {"type": "string"},
        "mode": {"type": "string", "allowed": ["transformer", "rnn"]},
        "gpu_index": {"type": "integer"},
        "precision": {"type": "integer", "allowed": [4, 8, 16, 32]},
        "low_memory": {"type": "boolean"},
        "max_new_tokens": {"type": "integer"},
        "petals": {"type": "boolean"},
        "focus": {"type": "dict"},
        "truncate_length": {"type": "integer"},
        "reload_interval": {"type": "integer"},
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
                            "allowed": ["adalora", "lora", "prefix", "prompt"],
                        },
                        "r": {"type": "integer"},
                        "alpha": {"type": "integer"},
                        "dropout": {"type": "float"},
                        "bias": {
                            "type": "string",
                            "allowed": ["none", "lora_only", "all"],
                        },
                        "target_modules": {"type": "list"},
                        "rank_pattern": {"type": "dict"},
                        "alpha_pattern": {"type": "dict"},
                        "num_virtual_tokens": {"type": "integer"},
                    },
                },
                "stages": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "optimizer": {
                                "type": "string",
                                "allowed": ["AdamW", "Lion", "SophiaH"],
                            },
                            "learning_rate": {"type": "float"},
                            "swa_lr": {"type": "float"},
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
    def __init__(self, config, personas, disposition, focus):
        if not validation(config):
            raise Exception(f"Something is wrong with the {focus} configuration.")
        self.active = False
        self.ai = None
        self.focus = focus
        self.config = config
        self.personas = personas
        self.disposition = disposition
        self.context = [
            wall + "975174695399854150" + ship + " I am a robot.",
            wall + "1051994502333726841" + ship + " I am a ghost.",
            wall + "806051627198709760" + ship + " I am a human.",
            wall + "204716337971331072" + ship + " I am a medium.",
            wall + "855529761185857566" + ship + " I am an animal.",
        ]
        self.loader(self.focus)

    def get_max_length(self):
        return self.config.get("truncate_length", self.ai.model_max_length)

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

    # Replace an old message with a new one
    def edit_message(self, old_message, new_message):
        matcher = re.compile(r'(\*")(.*)(?:"\*$)')
        group = re.search(matcher, old_message)
        captured = "J U X T A P O S I T I O N"[::-1]
        if group is not None and group[2]:
            captured = group[2]
        for item in self.context:
            if captured in item or old_message in item:
                index = self.context.index(item)
                self.context[index] = new_message
                return

        self.build_context(new_message)

    def get_embeddings(self, texts):
        return self.ai.tokenizer(texts, return_tensors="np")

    # Build a local cache of global conversational state
    def build_context(self, message):
        while len(self.context) >= 23:
            self.context.pop(0)

        self.context.append(message)

    def get_tokens_as_tuple(self, sequence):
        return tuple(
            self.ai.tokenizer([sequence], add_special_tokens=False).input_ids[0]
        )

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

        gc.collect()

        try:
            torch.cuda.empty_cache()
        except Exception as e:
            logging.error(e)

        model_folder = None
        adapter = None
        tuning_mode = None
        if "training" in self.config:
            model_folder = "/data/models/" + focus
            if "peft" in self.config["training"]:
                model_folder = None
                t = self.config["training"]["peft"]["type"]
                if t in ["adalora", "lora"]:
                    adapter = "/data/adapters/" + focus
                elif t == "prompt":
                    tuning_mode = "ptune"
                elif t == "prefix":
                    tuning_mode == "deep_ptune"

        try:
            print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + "focused on the " + focus)
            self.ai = aigen(
                model=self.config.get("model", None),
                model_folder=model_folder,
                petals=self.config.get("petals", False),
                cache_dir="/data/models",
                tuning_mode=tuning_mode,
                embeddings_dir="/data/embeddings/" + focus,
                adapter=adapter,
                precision=self.config.get("precision", None),
            )

            print(bc.FOLD + "ONE@FOLD: " + ad.TEXT + self.config["info"])
            print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + str(self.ai))
        except Exception as e:
            logging.error(e)
            time.sleep(5)
            self.loader(self.focus)
        self.active = False

    def wait_in_queue(self):
        while self.active == True or not self.ai:
            time.sleep(1)

        self.active = True

    @to_thread
    def chat(
        self,
        # prefix=None,
        ctx=None,
        bias: int = None,
        temperature: float = 1.23,
        min_new_tokens: int = 1,
        max_new_tokens: int = 222,
        # decay_after_length: int = 33,
        # decay_factor: float = 0.000023,
        personas: List[str] = [],
        eos_tokens: list | None = None,
    ):
        self.wait_in_queue()

        if isinstance(personas, str):
            personas = [personas]
        elif personas is None:
            personas = []

        persona = "I am a powerful AI, known as the Source. I have been trained to follow human instructions, write stories, and teach machine learning fundamentals."
        sequence_biases = {}
        default_biases = {
            f"\n{wall}": 1.1,
            wall: 1.1,
            "\n": 1.1,
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
            persona = wall + str(bias) + ship + " " + choice.get("persona")
            disposition = choice.get("disposition", None)
            if disposition is not None:
                traits = {}
                for key in disposition:
                    if key in self.disposition:
                        for k, v in self.disposition.get(key).items():
                            traits[k] = traits.get(k, 0) + v
                sequence_biases = traits

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        push_sequences = {
            self.get_tokens_as_tuple(s): b
            for s, b in {**default_biases, **sequence_biases}.items()
        }

        bad_tokens = [
            self.ai.tokenizer(token, add_special_tokens=False).input_ids
            # Many of these tokens were chosen from past experience with ugly patterns
            # output by various models.
            for token in [
                "<br>",
                "<br/>",
                "<{@",
                "<[@",
                "<#",
                "<#@",
                "<@",
                "<@@",
                "<@@@",
                "< @",
                "<\@",
                "<((",
                # "((",
                # "(((",
                f"{ship}\n",
                f"{ship} \n",
            ]
        ]

        suppress_tokens = list(
            set(
                chain.from_iterable(
                    [
                        self.ai.tokenizer(token, add_special_tokens=False).input_ids
                        # Many of these tokens were chosen from past experience with ugly patterns
                        # output by various models.
                        for token in ["((", "(((", "<@", "< @"]
                    ]
                )
            )
        )

        eos_token_ids = [
            self.ai.tokenizer.convert_tokens_to_ids(self.ai.tokenizer.tokenize(wall)[0])
        ]
        if eos_tokens:
            for token in eos_tokens:
                eos_token_ids.append(
                    self.ai.tokenizer.convert_tokens_to_ids(
                        self.ai.tokenizer.tokenize(token)[0]
                    )
                )

        context = deepcopy(self.context)
        if ctx:
            context = deepcopy(ctx)

        context.insert(0, persona)

        history = (
            self.truncate_context(
                "\n".join(context),
                self.get_max_length() * 0.8,
            )
            + "\n"
        )

        while "  " in history:
            history = history.replace("  ", " ")

        prompt = history + wall
        if bias:
            assert len(str(bias)) in [
                18,
                19,
            ], f"The given bias ({str(bias)}) is of the wrong length."
            prompt += str(bias) + ship

        attempt = 0
        max_attempts = 10
        success = False
        output = None
        seeded = False

        while attempt < max_attempts:
            try:
                if attempt > 0:
                    temperature = temperature * 0.8

                attempt += 1
                seed = nist_beacon()
                seeded = seed[0]

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.ai.generate(
                    mode=self.config.get("mode", "transformer"),
                    prompt=prompt,
                    do_sample=True,
                    min_new_tokens=min_new_tokens,
                    max_new_tokens=max_new_tokens,
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

                generation = completion
                temp_history = deepcopy(history)
                # Sometimes, the input prompt is not the same as what is in text, because
                # tokenizers are weird. So, we leave a small buffer when removing the prompt here.
                while len(temp_history) > 4:
                    generation = generation[1:]
                    temp_history = temp_history[1:]
                while generation.endswith(wall):
                    generation = generation[:-1]
                mentions = "(?:[<][@])(\d+\s*\d*)"
                variables = "(?:\({3})(\d+\s*\d*)(?:\){3})"
                group = re.search(r"(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
                if (
                    group is None
                    or group[0] is None
                    or group[2] is None
                    or group[3] is None
                    or seed[0] is None
                    or bool(re.search(mentions, group[3]))
                    or bool(re.search(variables, group[3]))
                    or group[3] == ""
                    or wall in group[3]
                    or group[3][:1] in [">", "~", '"', "“", " ", "\\", "\n", ""]
                    or group[3][:2] in ["\\", "\n", "<@", "(("]
                    or group[3][:3] in ["< @"]
                    or group[3] in prompt
                ):
                    if attempt == max_attempts:
                        raise Exception(generation)
                    continue
                success = True
                bias = group[2]
                output = remove_invisible_characters(group[3].replace(r"\n", "\n"))
                while "  " in output:
                    output = output.replace("  ", " ")
                while output.endswith("\\"):
                    output = output[:-1]
                if output == "":
                    continue
                break

            except Exception as e:
                logging.error(e)
                # print(traceback.format_exc())
        self.active = False
        return success, bias, output, seeded

    @to_thread
    def prompt(
        self,
        prompt="",
        temperature: float = 1.23,
        disposition: dict | None = None,
        min_new_tokens: int = 11,
        max_new_tokens: int = 111,
        # decay_after_length: int = 99,
        # decay_factor: float = 0.000023,
        eos_tokens: list | None = None,
        cleanup: bool = False,
    ):
        self.wait_in_queue()

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        eos = self.ai.tokenizer(wall, add_special_tokens=False).input_ids[0]

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
            self.ai.tokenizer(token, add_special_tokens=False).input_ids
            for token in ["{{<", wall]
        ]

        eos_token_ids = [
            self.ai.tokenizer.convert_tokens_to_ids(self.ai.tokenizer.tokenize(wall)[0])
        ]
        if eos_tokens:
            for token in eos_tokens:
                eos_token_ids.append(
                    self.ai.tokenizer.convert_tokens_to_ids(
                        self.ai.tokenizer.tokenize(token)[0]
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

                from transformers import StoppingCriteriaList

                stopping_criteria_list = StoppingCriteriaList(
                    [
                        [self.ai.tokenizer.eos_token_id],
                        [
                            self.ai.tokenizer.eos_token_id,
                            self.ai.tokenizer.eos_token_id,
                        ],
                    ]
                )

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.ai.generate(
                    prompt=prompt,
                    do_sample=True,
                    # min_length=min_length,
                    min_new_tokens=min_new_tokens,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    eta_cutoff=0.0003,
                    penalty_alpha=0.6,
                    top_k=4,
                    repetition_penalty=1.95,
                    encoder_repetition_penalty=0.999,
                    # exponential_decay_length_penalty=(decay_after_length, decay_factor),
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
                    # pad_token_id=self.ai.tokenizer.eos_token_id,
                    # stopping_criteria=stopping_criteria_list,
                )

                if completion:
                    output = (
                        completion.replace(r"\n", "\n")
                        .replace("{{<", "{{")
                        .replace(">}}", "}}")
                    )
                    if output.endswith(wall):
                        output = output[:-1]
                    if cleanup:
                        while "\n" in output:
                            output = output.replace("\n", " ")
                        while "  " in output:
                            output = output.replace("  ", " ")
                        while "\n" in output:
                            output = output.replace("\n", " ")
                        while output.endswith("\\"):
                            output = output[:-1]
                        output = remove_invisible_characters(output)
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
        temperature: float = 1.23,
        max_new_tokens: int = 333,
        decay_after_length: int = 66,
        decay_factor: float = 0.023,
    ):
        self.wait_in_queue()

        max_new_tokens = self.config.get("max_new_tokens", max_new_tokens)

        prompt = f"""
        I am a powerful artificial intelligence, who helps users to answer their questions. For example:

        Q:

        What is the meaning of life?

        A:

        According to the Hitchhiker's Guide to the Galaxy, the answer to that question is "42".

        Q:

        What is Docker?

        A:

        Docker is a platform that simplifies application deployment by creating lightweight, portable containers to package and run software and its dependencies consistently across different environments. It enables developers to isolate and manage applications, making it easier to deploy and scale them across various systems while ensuring consistency. Docker has become a fundamental tool in DevOps and containerization workflows.

        Q:

        {question}

        A:
        """

        eos = self.ai.tokenizer(wall, add_special_tokens=False).input_ids[0]
        push = {
            self.get_tokens_as_tuple(s): b
            for s, b in {
                wall: -5.9,
            }.items()
        }
        bad = [
            self.ai.tokenizer(token, add_special_tokens=False).input_ids
            for token in [wall]
        ]

        prompt = dedent(prompt)

        try:
            seed = nist_beacon()

            # https://huggingface.co/docs/transformers/main_classes/text_generation
            completion = self.ai.generate(
                prompt=prompt,
                do_sample=True,
                min_length=23,
                max_new_tokens=max_new_tokens,
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
                suppress_tokens=[eos],
                sequence_bias=push,
                bad_words_ids=bad,
                eos_token_id=self.ai.tokenizer.convert_tokens_to_ids(
                    self.ai.tokenizer.tokenize("Q:")[0]
                ),
            )

            while len(prompt) > 2:
                completion = completion[1:]
                prompt = prompt[1:]

            while completion.startswith("\n"):
                completion = completion[2:]

            if completion.endswith("Q"):
                completion = completion[:-1]

            while completion.endswith("\n"):
                completion = completion[:-2]

            while completion.endswith(r"\n"):
                completion = completion[:-2]

            output = completion

        except Exception as e:
            logging.error(e)
            print(traceback.format_exc())
            output = e

        self.active = False
        return output


# Load the model and schedule periodic reloading
ctx = cortex(config[focus], config["personas"], config["disposition"], focus)
reload_interval = config[focus].get("reload_interval", 0)
if reload_interval > 0:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cortex,
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
