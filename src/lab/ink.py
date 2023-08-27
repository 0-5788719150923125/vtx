import os
import random
import head
from utils import config, read_from_file, write_to_file

class Ink():
    def __init__(self):
        self.type = "confidants"
        self.role = None
        self.model_max_length = head.get_max_length()
        self.prompt = ""
        self.full_doc = ""
        self.replace_at_index = 0
        self.combine = False

    def get_length(self, string):
        tokens = head.ai.tokenizer(string, return_tensors="pt")["input_ids"]
        return len(tokens[0])

    def create_prompt(self, entry):
        path = f"/gen/{self.type}"
        if not os.path.exists(path):
            os.mkdir(path)

        self.role = entry.get('role')
        f = f"{path}/the-{self.role.lower()}.md" 
        if not os.path.exists(f):
            self.prompt = read_from_file(f"/src/lab/templates/{self.type}.tpl")
            for key in list(entry):
                value = entry.get(key)
                self.prompt = self.prompt.replace("{{" + key + "}}", value)
        else:
            self.prompt = read_from_file(f)
        self.full_doc = self.prompt

    def chunk_prompt(self):
        # self.model_max_length
        while self.get_length(self.prompt) > 128:
            print('prompt is too big!!')
            self.replace_at_index = random.randint(23, len(self.prompt))
            self.prompt = self.prompt[self.replace_at_index:]
            self.full_doc = self.full_doc[:self.replace_at_index]
            self.combine = True

    async def write(self):
        try:
            for t in list(config["kb"].get("data")):
                self.type = t
                for entry in config["kb"]["data"][t]:
                    self.create_prompt(entry)
                    self.chunk_prompt()
                    output = await head.gen(mode="prompt", prefix=self.prompt, max_new_tokens=33)
                    if self.combine:
                        cat = self.full_doc + output
                    else:
                        cat = output
                    print(cat)
                    write_to_file(path=f"/gen/{self.type}", file_name=f"the-{self.role.lower()}.md", content=cat)
        except Exception as e:
            print(e)