import importlib
import os
import threading
import time

# import memory
from common import ad, bc, config

# Quickly test stuff here
from lab import scratch

if os.environ.get("DEV_MODE", "false") == "true":
    import debugpy

    time.sleep(1)
    debugpy.listen(("0.0.0.0", 5678))


# This is the main loop
def main():
    allowed_services = [
        "source",
        "bit",
        "book",
        "smtp",
        "telegram",
        "matrix",
        "reddit",
        "discord",
        "twitch",
        "x",
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
            if config.get(service) and "enabled" in config.get(service):
                if config[service].get("enabled", True) == False:
                    continue
            if service not in tasks:
                module = importlib.import_module(f"lab.{service}")
                partial = {service: config.get(service), "personas": config["personas"]}
                task = threading.Thread(
                    target=getattr(module, "main"),
                    args=(partial,),
                    name=service,
                    daemon=True,
                )
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
