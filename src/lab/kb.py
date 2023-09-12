import os
import time
import random
import asyncio
import math
import logging
import head
from lab.reddit import manage_submission
from events import post_event
from utils import ad, bc, config, read_from_file, write_to_file


def orchestrate(config):
    allowed_types = ["confidants"]

    while True:
        ink = Ink()
        for t in list(config["kb"].get("types")):
            if t not in allowed_types:
                continue
            for entry in config["kb"]["types"][t]:
                chance = config["kb"].get("chance", 0)
                if "chance" in entry:
                    chance = entry.get("chance")
                if random.random() > chance:
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

    def get_length(self, string):
        tokens = head.ctx.ai.tokenizer(string, return_tensors="pt")["input_ids"]
        return len(tokens[0])

    def create_prompt(self, entry):
        path = f"/gen/{self.type}"
        if not os.path.exists(path):
            os.mkdir(path)

        if entry.get("prompt"):
            self.title = entry.get("title")
            self.prompt = entry.get("prompt")
        elif entry.get("role"):
            self.role = entry.get("role").lower().replace(" ", "-")

            f = f"{path}/the-{self.role}.md"
            title = self.role.replace("-", " ").title()
            self.title = f"{self.type.title()}: The {title}"
            self.prompt = read_from_file(f"/src/lab/templates/{self.type}.tpl")
            for key in list(entry):
                value = entry.get(key)
                if key == "role":
                    self.prompt = self.prompt.replace("{{role}}", value.title())
                elif key == "chance":
                    continue
                else:
                    self.prompt = self.prompt + f"\n{key.capitalize()}: {value}"

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
                path=f"/gen/{self.type}",
                file_name=f"the-{self.role}.md",
                content=content,
            )
            await manage_submission(title=self.title, content=content)
            # post_event(
            #     "kb_created",
            #     title=submission.title,
            #     description=submission.selftext,
            #     link=submission.shortlink,
            # )
            print(
                bc.CORE
                + "INK@KB: "
                + ad.TEXT
                + f"{self.type.title()}: The {self.title}"
            )

        except Exception as e:
            logging.error(e)
