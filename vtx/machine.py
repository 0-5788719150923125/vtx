from apscheduler.schedulers.asyncio import AsyncIOScheduler
import threading
import asyncio
import time
from utils import config
import random
import head
import lab

scheduler = AsyncIOScheduler()
scheduler.add_job(head.loader, "interval", minutes=60)
scheduler.start()

tasks = {}


# This is the main loop for the entire machine
@asyncio.coroutine
async def main(loop):
    head.ai = await head.loader()
    while True:
        # Prune completed tasks
        for task in tasks.copy():
            if tasks[task].done() or tasks[task].cancelled():
                del tasks[task]

        try:
            # Get configs, create tasks, and append to task queue
            for neuron in config["source"]:
                if "source-" + neuron not in tasks:
                    task = loop.create_task(lab.source.subscribe(neuron))
                    task.set_name("source-" + neuron)
                    tasks[task.get_name()] = task
        except Exception as e:
            print(e)

        if "telegram" in config and "telegram" not in tasks:
            task = loop.create_task(lab.telegram.subscribe())
            task.set_name("telegram")
            tasks[task.get_name()] = task

        if "reddit" in config:
            for subreddit in config["reddit"]:
                try:
                    watch = config["reddit"][subreddit].get("watch", False)
                except:
                    watch = False
                if watch and "reddit-" + subreddit not in tasks:
                    task = loop.create_task(lab.reddit.subscribe(subreddit))
                    task.set_name("reddit-" + subreddit)
                    tasks[task.get_name()] = task

            if random.random() < 0.023:
                task = loop.create_task(
                    lab.reddit.submission(config["reddit"]["prompt"])
                )
                task.set_name("reddit-submission")
                tasks[task.get_name()] = task

        if "discord" in config and "discord" not in tasks:
            task = loop.create_task(lab.discord.subscribe())
            task.set_name("discord")
            tasks[task.get_name()] = task

        await asyncio.sleep(66.6666)


# Start the main loop in a thread
def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))


loop = asyncio.get_event_loop()
t = threading.Thread(None, loop_in_thread, args=(loop,), daemon=True)

while True:
    time.sleep(5)
    if not t.is_alive():
        t.start()
