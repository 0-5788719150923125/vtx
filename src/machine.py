import threading
import time
import os
import importlib
from utils import config
# import hivemind
# from pytorch_lightning.strategies import HivemindStrategy
# from lightning_hivemind.strategy import HivemindStrategy

# This is the main loop
def main():

    allowed_services = [
        "source",
        "telegram",
        "telegraph",
        "reddit",
        "discord",
        "twitch",
        "twitter",
        "petals"
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

        time.sleep(66.6)

# Start the main loop in a thread
t = None
while True:
    time.sleep(5)
    if not t or not t.is_alive():
        t = threading.Thread(target=main, daemon=True)
        t.start()
