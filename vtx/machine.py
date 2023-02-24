from utils import config
import threading
import requests
import asyncio
import random
import head
import time
import lab

tasks = {}

# This is the main loop for the entire machine
@asyncio.coroutine
async def main(loop):

    # Load the AI model at startup
    if head.ai == None:
        head.ai = await head.loader()

    # Prune completed tasks
    for task in tasks.copy():
        if tasks[task].done():
            del tasks[task]

    # Get configs, create tasks, and append to task queue
    if "source" in config:
        for channel in config["source"]:
            if "watch" in config["source"][channel]:
                if config["source"][channel]["watch"] == True:
                    if "source-" + channel not in tasks:
                        task = loop.create_task(lab.source.subscribe(channel))
                        task.set_name("source-" + channel)
                        tasks[task.get_name()] = task

    if "telegram" in config:
        if "telegram" not in tasks:
            task = loop.create_task(lab.telegram.subscribe())
            task.set_name("telegram")
            tasks[task.get_name()] = task

    if "reddit" in config:
        for subreddit in config["reddit"]:
            if "watch" in config["reddit"][subreddit]:
                if config["reddit"][subreddit]["watch"] == True:
                    if "reddit-" + subreddit not in tasks:
                        task = loop.create_task(lab.reddit.subscribe(subreddit))
                        task.set_name("reddit-" + subreddit)
                        tasks[task.get_name()] = task

    if "discord" in config:
        if "discord" not in tasks:
            task = loop.create_task(lab.discord.subscribe())
            task.set_name("discord")
            tasks[task.get_name()] = task

    await asyncio.sleep(66.6666)
    await main(loop)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))


# Start the main loop in a thread
loop = asyncio.get_event_loop()
t = threading.Thread(None, loop_in_thread, args=(loop,), daemon=True)


# async def this_thing(loop):
#     loop.create_task(lab.telegram.create_bot_factory())


# loop.create_task(lab.telegram.create_bot_factory())
# asyncio.run()
# a = threading.Thread(None, lab.telegram.subscribe(), args=(loop,), daemon=True)
# a.start()

while True:
    time.sleep(5)
    if not t.is_alive():
        t.start()
