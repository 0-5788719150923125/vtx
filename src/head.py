import asyncio
import functools
import logging
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
from textwrap import dedent
from typing import List, Union

import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from cerberus import Validator
from transformers import AutoTokenizer, PreTrainedTokenizerFast

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".", "aigen"))
)

try:
    from aigen.aigen import aigen
except:
    from aig import aigen

import extensions
from common import (
    colors,
    config,
    cosine_similarity,
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
        "class": {"type": "string"},
        "mode": {"type": "string", "allowed": ["transformer", "rnn"]},
        "device_map": {"type": "string" or "dict"},
        "profile": {"type": "boolean"},
        "generation_profile": {"type": "string"},
        "gpu_index": {"type": "integer"},
        "precision": {
            "type": ["integer", "string"],
            "allowed": [4, 8, 16, "b16", 32, 64, 128],
        },
        "low_memory": {"type": "boolean"},
        "max_new_tokens": {"type": "integer"},
        "petals": {"type": "boolean"},
        "focus": {"type": "dict"},
        "context_length": {"type": "integer"},
        "reload_interval": {"type": "integer"},
        "adapters": {"type": "list"},
        "assistant": {"type": "dict"},
        "tokenizer": {"type": ["boolean", "string"]},
        "token_map": {"type": "dict"},
        "mode": {"type": "string"},
        "training": {
            "type": "dict",
            "schema": {
                "devices": {"type": ["string", "list"]},
                "device_map": {"type": ["string", "dict"]},
                "precision": {
                    "type": ["integer", "string"],
                    "allowed": [4, 8, 16, "b16", 32, 64, 128],
                },
                "resume": {"type": "boolean"},
                "regen": {"type": "boolean"},
                "refresh_logs": {"type": "boolean"},
                "corpus": {"type": "string"},
                "generate_every": {"type": "integer"},
                "checkpoint_every": {"type": "integer"},
                "save_every": {"type": "integer"},
                "gradient_checkpointing": {"type": "boolean"},
                "petals": {"type": "boolean"},
                "model_max_length": {"type": "integer"},
                "padding_side": {
                    "type": "string",
                    "allowed": ["left", "right"],
                },
                "name": {"type": "string"},
                "strategy": {"type": "string"},
                "initial_peers": {"type": "list"},
                "alpha": {"type": "integer"},
                "module_dropout": {"type": "float"},
                "rank_dropout": {"type": "float"},
                "type": {
                    "type": "string",
                    "allowed": [
                        "adalora",
                        "ia3",
                        "loha",
                        "lora",
                        "lokr",
                        "oft",
                        "prefix",
                        "prompt",
                        "standard",
                        "pretrain",
                    ],
                },
                "r": {"type": "integer"},
                "poly_type": {"type": "string"},
                "n_tasks": {"type": "integer"},
                "n_skills": {"type": "integer"},
                "n_splits": {"type": "integer"},
                "lora_alpha": {"type": "integer"},
                "lora_dropout": {"type": "float"},
                "use_rslora": {"type": "boolean"},
                "use_dora": {"type": "boolean"},
                "bias": {
                    "type": "string",
                    "allowed": ["none", "lora_only", "all"],
                },
                "target_modules": {"type": "list"},
                "save_embedding_layers": {"type": "boolean"},
                "feedforward_modules": {"type": "list"},
                "init_ia3_weights": {"type": "boolean"},
                "rank_pattern": {"type": "dict"},
                "alpha_pattern": {"type": "dict"},
                "num_virtual_tokens": {"type": "integer"},
                "optimizer": {"type": "string"},
                "num_cycles": {"type": "integer"},
                "prune": {"type": "float"},
                "overrides": {"type": "dict"},
                "learning_rate": {"type": "float"},
                "momentum": {"type": "float"},
                "use_lookahead": {"type": "boolean"},
                "k": {"type": "integer"},
                "bias_correction": {"type": "boolean"},
                "use_gc": {"type": "boolean"},
                "adanorm": {"type": "boolean"},
                "safeguard_warmup": {"type": "boolean"},
                "init_lora_weights": {"type": "string"},
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
                "finetune": {"type": "boolean"},
                "checkpoint": {"type": "boolean"},
                "batch_size": {"type": "integer"},
                "target_batch_size": {"type": "integer"},
                "gradient_accumulation_steps": {"type": "integer"},
                "tokenizer": {"type": ["boolean", "string"]},
                "equalize_datasets": {"type": "boolean"},
                "datasets": {"type": "dict"},
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
    def __init__(self, config, focus):
        if not validation(config[focus]):
            raise Exception(f"Something is wrong with the {focus} configuration.")
        self.active = False
        self.config = config[focus]
        self.transformers_config = config["transformers"]
        self.personas = config["personas"]
        self.disposition = config["disposition"]
        self.queue = []
        self.average_speed = []
        self.context = [
            {"bias": 975174695399854150, "message": "I am a robot."},
            {"bias": 1051994502333726841, "message": "I am a ghost."},
            {"bias": 806051627198709760, "message": "I am a human."},
            {"bias": 204716337971331072, "message": "I am a medium."},
            {"bias": 855529761185857566, "message": "I am an animal."},
        ]

        self.assistant = None
        self.teacher = self.loader(self.config, focus)
        if self.config.get("assistant") is not None:
            self.assistant = self.loader(
                self.config["assistant"], focus, parent="assistant"
            )

    def loader(self, config, focus="assistant", parent=focus):
        print(colors.BLUE + "ONE@FOLD: " + colors.WHITE + "focused on the " + focus)

        time.sleep(2)

        model_info = config.get("info", "to the regional manager")
        print(f"{colors.BLUE}ONE@FOLD:{colors.WHITE} {model_info}")

        while self.active == True:
            time.sleep(1)

        self.active = True

        time.sleep(5)

        adapters = None
        model_folder = None
        adapter_dir = "/data/adapters/" + focus
        embeddings_dir = "/data/embeddings/" + focus
        tuning_mode = None
        pre_seq_len = 24
        tokenizer = None
        tokenizer_folder = None
        if "training" in config:
            t = config["training"].get("type", "standard")
            if t not in ["standard", "pretrain"]:
                adapters = config.get("adapters", ["base"])
                for adapter in adapters:
                    if not os.path.exists(
                        f"{adapter_dir}/{adapter}/adapter_model.bin"
                    ) and not os.path.exists(
                        f"{adapter_dir}/{adapter}/adapter_model.safetensors"
                    ):
                        adapter_dir = "/adapters/" + focus
                        break
            elif t == "prompt":
                tuning_mode = "ptune"
                pre_seq_len = t.get("num_virtual_tokens", pre_seq_len)
            elif t == "prefix":
                tuning_mode == "deep_ptune"
                pre_seq_len = t.get("num_virtual_tokens", pre_seq_len)
            else:
                model_folder = "/data/models/" + focus
                if config["training"].get("corpus"):
                    tokenizer_folder = model_folder

        if "tokenizer" in config:
            tokenizer = AutoTokenizer.from_pretrained(config["tokenizer"])
        try:
            prototype = aigen(
                model=config.get("model"),
                model_folder=model_folder,
                tokenizer=tokenizer,
                tokenizer_folder=tokenizer_folder,
                device_map=config.get("device_map", "auto"),
                petals=config.get("petals", False),
                cache_dir="/data/models",
                tuning_mode=tuning_mode,
                embeddings_dir=embeddings_dir,
                adapter_dir=adapter_dir,
                adapters=adapters,
                merge_adapters=True,
                precision=config.get("precision", 32),
                pre_seq_len=pre_seq_len,
            )

            for k, v in config.get("token_map", {}).items():
                setattr(
                    prototype.tokenizer, k, prototype.tokenizer.convert_ids_to_tokens(v)
                )

            if config.get("context_length") is not None:
                setattr(
                    prototype.model.config,
                    "context_length",
                    config.get("context_length"),
                )

            focus = "assistant" if parent == "assistant" else focus
            prototype.optimize_for_inference()

            print(f"{colors.GREEN}ONE@ROOT:{colors.WHITE} {str(prototype)}")

            time.sleep(3)
        except Exception as e:
            logging.error(traceback.format_exc())
            time.sleep(5)
            prototype = self.loader(focus)

        self.active = False

        return prototype

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
        while length >= max_tokens:
            joined = joined[10:]
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

    def wait_in_queue(self, priority=False):
        self.queue.append({"me": self, "priority": priority})

        while True:
            time.sleep(1)
            if self.teacher is None:
                continue
            if self.active:
                continue
            skip = False
            for value in self.queue:
                if value["priority"]:
                    skip = True
                    if priority:
                        skip = False
                    break

            if skip:
                continue

            if self.active:
                continue

            self.active = True
            return

    def remove_from_queue(self, priority=False):
        self.active = False
        if priority:
            for value in self.queue:
                if value["priority"]:
                    self.queue.pop(self.queue.index(value))
                    return
        self.queue.pop(0)

    def truncate_long_sequences(self, text, max_length=20):
        result = ""
        current_sequence = ""

        for char in text:
            if char.isspace():
                result += current_sequence + char
                current_sequence = ""
            else:
                current_sequence += char

                if len(current_sequence) > max_length:
                    return result.rstrip()

        return result + current_sequence

    def check_similarity(self, ctx, message, threshold=0.7):
        for memory in ctx:
            score = cosine_similarity(memory["message"], message)
            if score > threshold:
                return False
        return True

    def _remove_words_and_right(self, text, words_to_remove):
        for word in words_to_remove:
            index = text.lower().find(word.lower())
            if index != -1:
                text = text[:index]
        return text.strip()

    @to_thread
    def chat(
        self,
        ctx=None,
        priority: bool = False,
        bias: int = None,
        start_with: str = None,
        temperature: float = None,
        min_new_tokens: int = None,
        max_new_tokens: int = None,
        personas: List[str] = [],
        eos_tokens: list | None = None,
        generation_profile: str = "default",
    ):
        self.wait_in_queue(priority)

        tokenizer = self.teacher.tokenizer

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
            tokenizer(token, add_special_tokens=False).input_ids
            for token in [
                f"{ship}\n",
                f"{ship} \n",
            ]
        ]

        suppress_tokens = list(
            set(
                chain.from_iterable(
                    [
                        tokenizer(token, add_special_tokens=False).input_ids
                        # Suppress ugly patterns the model may sometimes bias towards.
                        for token in ["((", "(((", "<@", "< @"]
                    ]
                )
            )
        )

        eos_token_ids = [tokenizer.convert_tokens_to_ids(tokenizer.tokenize(wall)[0])]
        if eos_tokens:
            for token in eos_tokens:
                eos_token_ids.append(
                    tokenizer.convert_tokens_to_ids(tokenizer.tokenize(token)[0])
                )

        context = deepcopy(ctx) if ctx else deepcopy(self.context)

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

        if start_with:
            prompt += start_with

        attempt = 0
        max_attempts = 10
        success = False
        seeded = False
        output = False

        start = time.time()

        generation_config = self.transformers_config["generation"][
            self.config.get("generation_profile", generation_profile)
        ]
        temperature = (
            temperature
            if temperature is not None
            else generation_config.get("temperature", 0.95)
        )
        new_tokens = max_new_tokens or generation_config.get("max_new_tokens", 333)

        while attempt < max_attempts:
            try:
                if attempt > 0:
                    temperature *= 1.1

                attempt += 1
                seed = nist_beacon()
                seeded = seed[0]

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.teacher.generate(
                    prompt=prompt,
                    mode=self.config.get("mode", "transformer"),
                    generation_config=generation_config,
                    do_sample=generation_config.get("do_sample", True),
                    temperature=temperature,
                    min_new_tokens=(
                        min_new_tokens
                        if min_new_tokens is not None
                        else generation_config.get("min_new_tokens", 1)
                    ),
                    max_new_tokens=new_tokens,
                    exponential_decay_length_penalty=(new_tokens, -0.11),
                    max_time=360,
                    seed=seed[1],
                    use_cache=True,
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    sequence_bias=push_sequences,
                    bad_words_ids=bad_tokens,
                    suppress_tokens=suppress_tokens,
                    eos_token_id=eos_token_ids,
                    # stop_strings=[wall],
                    assistant=self.assistant.model if self.assistant else None,
                )

                generation = "\n".join(
                    completion.splitlines()[len(history.splitlines()) :]
                ).rstrip(wall)
                urls = r"http\S+"
                mentions = "(?:[<][@])(\d+\s*\d*)"
                variables = "(?:\({3})(\d+\s*\d*)(?:\){3})"
                group = re.search(r"(¶{1})(\d{2,23})(?::\s?>\s*)(.*)", generation)
                if (
                    group is None
                    or group[2] is None
                    or group[3] is None
                    or group[3] in prompt
                    or wall in group[3]
                    or bool(re.search(urls, group[3]))
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
                if not self.check_similarity(context, group[3]):
                    continue
                if output == "(":
                    continue

                output = self.truncate_long_sequences(output, 20)
                output = self._remove_words_and_right(
                    output,
                    ["CONTEXT:", "INPUT:", "OUTPUT:", "SYSTEM:", "USER:", "ASSISTANT:"],
                )

                if output == "":
                    continue

                bias = group[2]
                success = True
                break

            except Exception as e:
                import traceback

                print(traceback.format_exc())

        if self.config.get("profile", False):
            self.average_speed.append(time.time() - start)
            while len(self.average_speed) > 10000:
                for _ in range(10):
                    self.average_speed.pop(0)
            if len(self.average_speed) % 10 == 0:
                print(
                    f"Average speed: {statistics.mean(self.average_speed)}, Number of samples: {len(self.average_speed)}"
                )

        self.remove_from_queue(priority)
        return success, bias, output, seeded

    @to_thread
    def prompt(
        self,
        prompt="",
        priority: bool = False,
        temperature: float = None,
        disposition: dict | None = None,
        min_new_tokens: int = None,
        max_new_tokens: int = None,
        eos_tokens: list | None = None,
        cleanup: bool = False,
        generation_profile: str = "longform",
        forbidden_chars: list = [],
    ):
        self.wait_in_queue(priority)

        sequence_biases = {wall: -20.0}
        if disposition is not None:
            traits = {}
            for key in disposition:
                if key in self.disposition:
                    for k, v in self.disposition.get(key).items():
                        traits[k] = traits.get(k, 0) + v
            sequence_biases = {**sequence_biases, **traits}

        push = {self.get_tokens_as_tuple(s): b for s, b in sequence_biases.items()}
        bad_tokens = [
            self.teacher.tokenizer(token, add_special_tokens=False).input_ids
            for token in ["{{<", wall, f"\n{wall}", f"\n\n{wall}"]
        ]

        # suppress_tokens = list(
        #     set(
        #         chain.from_iterable(
        #             [
        #                 self.teacher.tokenizer(
        #                     token, add_special_tokens=False
        #                 ).input_ids
        #                 # Suppress ugly patterns the model may sometimes bias towards.
        #                 for token in [
        #                     "#",
        #                     "##",
        #                     "###",
        #                 ]
        #             ]
        #         )
        #     )
        # )

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

        generation_config = self.transformers_config["generation"][generation_profile]
        temperature = (
            temperature
            if temperature is not None
            else generation_config.get("temperature", 0.95)
        )
        new_tokens = max_new_tokens or generation_config.get("max_new_tokens", 333)

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            try:
                seed = nist_beacon()

                if attempt > 0:
                    temperature *= 1.1

                attempt += 1

                # https://huggingface.co/docs/transformers/main_classes/text_generation
                completion = self.teacher.generate(
                    prompt=prompt,
                    mode=self.config.get("mode", "transformer"),
                    generation_config=generation_config,
                    do_sample=generation_config.get("do_sample", True),
                    dola_layers=generation_config.get("dola_layers", None),
                    temperature=temperature,
                    min_new_tokens=(
                        min_new_tokens
                        if min_new_tokens is not None
                        else generation_config.get("min_new_tokens", 1)
                    ),
                    max_new_tokens=new_tokens,
                    max_time=360,
                    seed=seed[1],
                    use_cache=True,
                    renormalize_logits=True,
                    remove_invalid_values=True,
                    sequence_bias=push,
                    # suppress_tokens=suppress_tokens,
                    bad_words_ids=bad_tokens,
                    eos_token_id=eos_token_ids,
                    forbidden_chars=forbidden_chars,
                    stop_strings=["void:"],
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

        self.remove_from_queue(priority)
        return output


# Load the model and schedule periodic reloading
ctx = Cortex(config, focus)
reload_interval = config[focus].get("reload_interval", 0)
if reload_interval > 0:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        Cortex,
        args=(config, focus),
        trigger="interval",
        minutes=reload_interval,
    )
    scheduler.start()
