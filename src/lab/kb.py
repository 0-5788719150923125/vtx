import asyncio
import logging
import math
import os
import random
import time

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

    allowed_types = ["confidants", "prose"]

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
        time.sleep(60)


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
        self.stage = ""
        self.full_doc = ""
        self.replace_at_index = 0
        self.combine = False
        self.dir = ""
        self.file = ""
        self.tags = []

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
                    self.prompt = self.prompt + f"\n{key.capitalize()}: {value}"
        else:
            self.title = entry.get("title")
            self.prompt = "# " + self.title + "\n---\n" + entry.get("prompt")
            self.file = deterministic_short_hash(self.title, length=7) + ".md"
            f = f"{self.dir}/{self.file}"

        self.stage = self.prompt
        if os.path.exists(f):
            self.stage = read_from_file(f)
        else:
            self.created = True
        self.full_doc = self.stage

    def chunk_prompt(self):
        partial = math.floor(self.model_max_length * 0.8)
        while self.get_length(self.stage) > partial:
            self.replace_at_index = random.randint(len(self.prompt), len(self.stage))
            self.stage = self.stage[: self.replace_at_index]
            self.full_doc = self.full_doc[self.replace_at_index :]
            self.combine = True

    async def write(self, t, entry):
        try:
            self.type = t
            self.tags = entry.get("tags", [])
            self.create_prompt(entry)
            self.chunk_prompt()
            output = await head.ctx.prompt(prompt=self.stage, max_new_tokens=33)
            if output[0] == False:
                print(output[1])
                return
            content = output
            if self.combine:
                self.combine = False
                content = output + self.full_doc
            write_to_file(
                path=self.dir,
                file_name=self.file,
                content=content,
            )
            post_event(
                "kb_updated",
                title=self.title,
                content=content,
                tags=self.tags,
            )
            print(bc.CORE + "ONE@KB: " + ad.TEXT + self.title)

        except Exception as e:
            logging.error(e)
