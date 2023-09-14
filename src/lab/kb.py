import os
import time
import random
import asyncio
import math
import logging
import head
from events import post_event
from utils import (
    ad,
    bc,
    config,
    deterministic_short_hash,
    read_from_file,
    write_to_file,
)


def orchestrate(config):
    allowed_types = ["confidants", "prose"]

    while True:
        ink = Ink()
        for t in list(config["kb"].get("types")):
            if t not in allowed_types:
                continue
            for entry in config["kb"]["types"][t]:
                frequency = config["kb"].get("frequency", 0)
                if "frequency" in entry:
                    frequency = entry.get("frequency")
                if random.random() > frequency:
                    continue
                asyncio.run(ink.write(t, entry))
        time.sleep(60)


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
        self.dir = f"/gen/{self.type}"
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        if entry.get("role"):
            self.role = entry.get("role").lower().replace(" ", "-")
            self.tags.append("role")

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
            self.prompt = entry.get("prompt")
            self.file = deterministic_short_hash(self.title, length=7) + ".md"
            f = f"{self.dir}/{self.file}"

        self.stage = self.prompt
        if os.path.exists(f):
            self.stage = read_from_file(f)
        else:
            self.created = True
        self.full_doc = self.stage

    def chunk_prompt(self):
        three_quarters = math.floor((self.model_max_length / 4)) * 3
        while self.get_length(self.stage) > three_quarters:
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
                content = self.full_doc + output
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
            print(bc.CORE + "INK@KB: " + ad.TEXT + self.title)

        except Exception as e:
            logging.error(e)
