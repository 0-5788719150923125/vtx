import os
import head
from utils import read_from_file, write_to_file

template_types = {
    "confidants": {
        "role": "Kunist",
        "name": "Emilia Benno Sameyn"
    }
}

class Ink():
    def __init__(self):
        self.type = "confidants"
        self.role = None
        self.model_max_length = head.get_max_length()
        self.prompt = ""

    def get_length(self, string):
        tokens = head.ai.tokenizer(string, return_tensors="pt")["input_ids"]
        return len(tokens[0])

    def create_prompt(self):
        path = f"/gen/{self.type}"
        if not os.path.exists(path):
            os.mkdir(path)

        self.role = template_types[self.type].get('role')
        f = f"{path}/the-{self.role.lower()}.md" 
        if not os.path.exists(f):
            self.prompt = read_from_file(f"/src/lab/templates/{self.type}.tpl")
            for key in list(template_types[self.type]):
                value = template_types[self.type].get(key)
                self.prompt = self.prompt.replace("{{" + key + "}}", value)
        else:
            self.prompt = read_from_file(f)

    async def write(self):
        try:
            self.create_prompt()
            prompt_length = self.get_length(self.prompt)
            if prompt_length > self.model_max_length:
                print('prompt is too big!!')
            else:
                print('prompt fits!!')

            output = await head.gen(mode="prompt", prefix=self.prompt, max_new_tokens=512)
            print(output)
            write_to_file(path=f"/gen/{self.type}", file_name="the-kunist.md", content=output)
        except Exception as e:
            print(e)