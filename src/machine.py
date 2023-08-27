import threading
import time
import os
import importlib
from utils import ad, bc, config
# from lightning_hivemind.strategy import HivemindStrategy

# import torch
# from transformers import AutoTokenizer, GenerationConfig, AutoModelForCausalLM
# from petals import AutoDistributedModelForCausalLM
# from peft import PeftModel, PeftConfig

# # model_name = "stabilityai/StableBeluga-7B"
# model_name = "bigscience/bloom-560m"

# model = AutoDistributedModelForCausalLM.from_pretrained(model_name, cache_dir="models", torch_dtype=torch.float32, active_adapter="adapters/soul")
# tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir="models", padding_side="left")
# # model = AutoModelForCausalLM.from_pretrained(model_name, cache_dir="models", torch_dtype=torch.float32)

# params = GenerationConfig(
#         max_time=360,
#         max_new_tokens=33
#     )
# # model = PeftModel.from_pretrained(model, "adapters/soul")

# inputs = tokenizer("A cat sat", return_tensors="pt")["input_ids"]

# outputs = model.generate(inputs=inputs, max_length=2048, generation_config=params)
# # outputs = model.generate(input_ids=inputs, max_new_tokens=9, num_beams=3)
# print(tokenizer.decode(outputs[0]))  # A cat sat on a mat...

# This is the main loop
def main():

    allowed_services = [
        "source",
        "telegram",
        # "telegraph",
        "reddit",
        "discord",
        "twitch",
        "twitter",
        "matrix",
        "kb"
    ]

    tasks = {}

    while True:
        # Prune completed tasks
        for task in list(tasks):
            if not tasks[task].is_alive():
                tasks.pop(task)

        # Get configs, create tasks, and append to task queue
        for service in config:
            if service not in allowed_services:
                continue
            if service not in tasks:
                module = importlib.import_module(f"lab.{service}")
                task = threading.Thread(target=getattr(module, "orchestrate"), args=(config[service],))
                task.name = service
                task.start()
                tasks[task.name] = task
                print(bc.ROOT + f"ONE@{service.upper()}: " + ad.TEXT + "connected")

        time.sleep(66.6)

# Start the main loop in a thread
t = None
while True:
    time.sleep(5)
    if not t or not t.is_alive():
        t = threading.Thread(target=main, daemon=True)
        t.start()
