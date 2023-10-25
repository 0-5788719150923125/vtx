import asyncio
import logging
import math
import os
import random
import re
import time

import yaml
from cerberus import Validator

import head
from common import (
    ad,
    bc,
    config,
    deterministic_short_hash,
    read_from_file,
    write_to_file,
)
from events import post_event


def main(config):
    result = validation(config["kb"])
    if not result:
        return

    allowed_types = ["confidants", "prose", "theory"]

    while True:
        ink = Ink()
        for t in list(config["kb"].get("types")):
            if t not in allowed_types:
                continue
            for entry in config["kb"]["types"][t]:
                frequency = entry.get("frequency", config["kb"].get("frequency", 0))
                if random.random() > frequency:
                    continue
                asyncio.run(ink.write(t, entry))
        time.sleep(66.6)


if __name__ == "main":
    main(config)


def validation(config):
    schema = {
        "frequency": {"type": "float"},
        "types": {
            "type": "dict",
            "schema": {
                "prose": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "schema": {
                            "title": {"type": "string"},
                            "prompt": {"type": "string"},
                            "frequency": {"type": "float"},
                            "tags": {"type": "list"},
                        },
                    },
                },
                "confidants": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        "allow_unknown": True,
                        "schema": {
                            "role": {"type": "string"},
                        },
                    },
                },
                "theory": {
                    "type": "list",
                    "schema": {
                        "type": "dict",
                        # "allow_unknown": True,
                        "schema": {
                            "title": {"type": "string"},
                            "frequency": {"type": "float"},
                            "weight": {"type": "integer"},
                            "alias": {"type": "list"},
                            "subtype": {"type": "list"},
                            "creation": {"type": "string"},
                            "stage": {"type": "string"},
                            "trigger": {"type": "string"},
                            "eco": {"type": "string"},
                            "tags": {"type": "list"},
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


class Ink:
    def __init__(self):
        self.type = "confidants"
        self.role = None
        self.model_max_length = head.ctx.get_max_length()
        self.title = ""
        self.prompt = ""
        self.staged = ""
        self.full_doc = ""
        self.replace_at_index = 0
        self.combine = False
        self.dir = ""
        self.file = ""
        self.tags = []
        self.new_tokens = 33

    def get_length(self, string):
        tokens = head.ctx.ai.tokenizer(string, return_tensors="pt")["input_ids"]
        return len(tokens[0])

    def create_prompt(self, entry):
        self.dir = f"/book/content/{self.type}"
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
            with open(os.path.join(self.dir, "_index.md"), "w") as file:
                pass

        if entry.get("role"):
            self.role = entry.get("role").lower().replace(" ", "-")
            self.tags.append("ink")
            self.tags.append("roles")

            self.file = f"the-{self.role}.md"
            f = f"{self.dir}/{self.file}"

            title = self.role.replace("-", " ").title()
            self.title = f"{self.type.title()}: The {title}"
            self.prompt = read_from_file(f"/src/lab/templates/{self.type}.tpl")
            for key in list(entry):
                value = entry.get(key)
                if key == "role":
                    self.prompt = self.prompt.replace("{{role}}", value.title())
                elif key == "frequency":
                    continue
                else:
                    if isinstance(value, list):
                        value.sort()
                        joined = "\n  - ".join(value)
                        value = f"\n  - {joined}"
                    self.prompt = self.prompt + f"\n{key.capitalize()}: {value}"
        elif self.type == "theory":
            title = entry.get("title")
            self.title = f"{self.type.title()}: {title}"
            self.prompt = read_from_file(f"/src/lab/templates/{self.type}.tpl")
            for key in list(entry):
                value = entry.get(key)
                if key == "frequency":
                    continue
                else:
                    if isinstance(value, list):
                        value.sort()
                        joined = "\n  - ".join(value)
                        value = f"\n  - {joined}"
                    self.prompt = self.prompt.replace(f"{{{{{key}}}}}", str(value))
            self.file = deterministic_short_hash(self.title, length=7) + ".md"
            f = f"{self.dir}/{self.file}"
        else:
            self.title = entry.get("title")
            self.prompt = "# " + self.title + "\n---\n" + entry.get("prompt")
            self.file = deterministic_short_hash(self.title, length=7) + ".md"
            f = f"{self.dir}/{self.file}"

        self.staged = self.prompt
        if os.path.exists(f):
            self.staged = read_from_file(f)
        else:
            self.new_tokens = 333
        self.full_doc = self.staged

    def chunk_prompt(self):
        partial = math.floor(self.model_max_length * 0.8)
        while self.get_length(self.staged) > partial:
            self.replace_at_index = random.randint(len(self.prompt), len(self.staged))
            # print(f"replacing at index {self.replace_at_index}")
            self.staged = self.staged[: self.replace_at_index]
            self.combine = True

    async def write(self, t, entry):
        try:
            self.type = t
            self.tags = entry.get("tags", [])
            self.create_prompt(entry)
            self.chunk_prompt()
            output = await head.ctx.prompt(
                prompt=self.staged,
                max_new_tokens=self.new_tokens,
                # decay_after_length=33,
                # decay_factor=-0.23,
            )
            if output == False:
                return
            content = output
            if self.combine:
                self.combine = False
                # content = output + self.full_doc[: self.replace_at_index]
                # print(self.full_doc[: self.replace_at_index])
            write_to_file(
                path=self.dir,
                file_name=self.file,
                content=content,
            )
            pattern = re.compile(r"^(---\n.+\#{2}\sRECORD)", re.DOTALL)
            group = re.search(pattern, content)
            clean = content
            if group is not None and group[0] is not None:
                clean = content.replace(group[0], "## RECORD")
            post_event(
                "kb_updated",
                title=self.title,
                content=clean,
                tags=self.tags,
            )
            print(bc.CORE + "ONE@KB: " + ad.TEXT + self.title)

        except Exception as e:
            logging.error(e)
            import traceback

            print(traceback.format_exc())
