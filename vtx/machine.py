from apscheduler.schedulers.asyncio import AsyncIOScheduler
import threading
import asyncio
import time
from utils import config, propulsion
import random
import head
import lab

# scheduler = AsyncIOScheduler()
# scheduler.add_job(head.loader, "interval", minutes=30)
# scheduler.start()

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

        # Get configs, create tasks, and append to task queue
        for focus in config["source"]:
            if f"source-streamer-{focus}" not in tasks:
                task = loop.create_task(lab.source.streaming(focus))
                task.set_name(f"source-streamer-{focus}")
                tasks[task.get_name()] = task
            if f"source-watcher-{focus}" not in tasks:
                task = loop.create_task(lab.source.watcher(focus))
                task.set_name(f"source-watcher-{focus}")
                tasks[task.get_name()] = task

        if "telegram" in config and "telegram" not in tasks:
            task = loop.create_task(lab.telegram.subscribe())
            task.set_name("telegram")
            tasks[task.get_name()] = task

        if "telegraph" in config and "telegraph" not in tasks:
            task = loop.create_task(lab.telegraph.orchestrate(config["telegraph"]))
            task.set_name("telegraph")
            tasks[task.get_name()] = task

        if "reddit" in config:
            task = loop.create_task(lab.reddit.orchestrate(config))
            task.set_name("reddit")
            tasks[task.get_name()] = task

        if "discord" in config and "discord" not in tasks:
            task = loop.create_task(lab.discord.subscribe())
            task.set_name("discord")
            tasks[task.get_name()] = task

        if "twitch" in config and "twitch" not in tasks:
            task = loop.create_task(lab.twitch.subscribe())
            task.set_name("twitch")
            tasks[task.get_name()] = task

        if "twitter" in config and "twitter" not in tasks and random.random() < 0.00059:
            topics = config["twitter"].get("topics", ["AI alignment"])
            task = loop.create_task(
                lab.twitter.send(
                    await head.gen(
                        prefix=random.choice(topics),
                        max_new_tokens=64,
                        decay_after_length=6,
                        decay_factor=0.0023,
                        mode="prompt",
                    )
                )
            )
            task.set_name("twitter")
            tasks[task.get_name()] = task

        await asyncio.sleep(66.6)


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
