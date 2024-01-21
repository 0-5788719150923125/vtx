import importlib
import os
import threading
import time

import memory
from common import colorize_yaml, colors, config

# test code in production here
from lab import dev

print(colorize_yaml(config))


# This is the main loop
def main():
    allowed_services = [
        "api",
        "ipfs",
        "source",
        "urbit",
        "book",
        "smtp",
        "telegram",
        "matrix",
        "reddit",
        "discord",
        "twitch",
        "horde",
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
                print(
                    colors.GREEN
                    + f"ONE@{service.upper()}: "
                    + colors.WHITE
                    + "connected"
                )

        time.sleep(66.6)


main()
