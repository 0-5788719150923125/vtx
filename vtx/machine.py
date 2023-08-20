import threading
import asyncio
import time
import os
import importlib
from utils import config
import head

from apscheduler.schedulers.background import BackgroundScheduler

focus = os.environ["FOCUS"]
head.ai = head.loader(focus)

scheduler = BackgroundScheduler()
scheduler.add_job(head.loader, args=[focus], trigger="interval", minutes=30)
scheduler.start()

# This is the main loop for the entire machine
def main():

    tasks = {}

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

    while True:
        # Prune completed tasks
        for task in list(tasks):
            if tasks[task].is_alive() or tasks[task].is_alive():
                tasks[task].join()
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
