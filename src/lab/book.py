import asyncio
import logging
import math
import os
import random
import re
import time

import psutil
import yaml
from cerberus import Validator

import head
from common import (
    colors,
    config,
    deterministic_short_hash,
    read_from_file,
    run_shell_command,
    write_to_file,
)
from events import post_event
from pipe import producer, queue

if __name__ == "main":
    main()


def main(config):
    book_config = config["book"]
    result = validation(book_config)
    if not result:
        return

    allowed_types = ["confidants", "prose", "theory"]

    while True:
        ink = Ink()
        if book_config.get("site", False):
            build_static_website()
        for t in list(book_config.get("types")):
            if t not in allowed_types:
                continue
            for entry in book_config["types"][t]:
                frequency = entry.get("frequency", book_config.get("frequency", 0))
                if random.random() > frequency:
                    continue
                asyncio.run(ink.write(t, entry))
        time.sleep(66.6)


if __name__ == "main":
    main(config)


def validation(config):
    schema = {
        "site": {"type": "boolean"},
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
        self.dir = ""
        self.file = ""
        self.tags = []
        self.new_tokens = 111

    def get_length(self, string):
        tokens = head.ctx.teacher.tokenizer(string, return_tensors="pt")["input_ids"]
        return len(tokens[0])

    def create_prompt(self, entry):
        self.dir = f"/book/content/{self.type}"
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
            with open(os.path.join(self.dir, "_index.md"), "w") as file:
                pass

        if self.type == "confidants":
            self.role = entry.get("role").lower().replace(" ", "-")
            self.tags.append("roles")
            self.tags.append("ink")

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
            self.staged = self.staged[: self.replace_at_index]

    async def write(self, t, entry):
        try:
            self.type = t
            self.tags = entry.get("tags", [])
            self.create_prompt(entry)
            self.chunk_prompt()
            output = await head.ctx.prompt(
                prompt=self.staged,
                min_new_tokens=self.new_tokens - 33,
                max_new_tokens=self.new_tokens,
                eos_tokens=[".", "?", "!", '."', '?"', '!"'],
            )
            if output == False:
                return
            write_to_file(
                path=self.dir,
                file_name=self.file,
                content=output,
            )
            pattern = re.compile(r"^(---\n.+\#{2}\sRECORD)", re.DOTALL)
            group = re.search(pattern, output)
            clean = output
            if group is not None and group[0] is not None:
                clean = output.replace(group[0], "## RECORD")
            elif self.type == "prose":
                clean = "\n\n".join(output.splitlines()[2:])
            print(colors.RED + "ONE@KB: " + colors.WHITE + self.title)
            producer(
                queue,
                {
                    "event": "book_updated",
                    "source": "book",
                    "title": self.title,
                    "content": clean,
                    "tags": self.tags,
                },
            )

        except Exception as e:
            logging.error(e)
            import traceback

            print(traceback.format_exc())


def build_static_website():
    alive = False
    for process in psutil.process_iter(["pid", "name"]):
        if process.info["name"] != "hugo":
            continue
        if process.status() == "zombie":
            continue
        alive = True
    time.sleep(6.66)
    if not alive:
        run_shell_command(
            "hugo server --source '/book' --port 42000 --noBuildLock --quiet"
        )
