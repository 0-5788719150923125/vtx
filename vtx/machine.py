from apscheduler.schedulers.asyncio import AsyncIOScheduler
import threading
import asyncio
import time
from utils import config, propulsion
import random
import head
import lab

scheduler = AsyncIOScheduler()
scheduler.add_job(head.loader, "interval", minutes=59)
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
                if "chance" in config["reddit"][subreddit]:
                    if "reddit-" + subreddit not in tasks:
                        task = loop.create_task(
                            lab.reddit.subscribe_comments(subreddit)
                        )
                        task.set_name("reddit-" + subreddit)
                        tasks[task.get_name()] = task
                    if "reddit-" + subreddit + "-submissions" not in tasks:
                        task = loop.create_task(
                            lab.reddit.subscribe_submissions(subreddit)
                        )
                        task.set_name("reddit-" + subreddit + "-submissions")
                        tasks[task.get_name()] = task
            if random.random() < 0.0059:
                task = loop.create_task(
                    lab.reddit.submission(config["reddit"]["prompt"])
                )
                task.set_name("reddit-submission")
                tasks[task.get_name()] = task

        if "discord" in config and "discord" not in tasks:
            task = loop.create_task(lab.discord.subscribe())
            task.set_name("discord")
            tasks[task.get_name()] = task

        if "twitch" in config and "twitch" not in tasks:
            task = loop.create_task(lab.twitch.subscribe())
            task.set_name("twitch")
            tasks[task.get_name()] = task

        if "twitter" in config and "twitter" not in tasks and random.random() < 0.0059:
            topic = config["twitter"].get("topic", "AI alignment")
            task = loop.create_task(
                lab.twitter.send(
                    await head.predict(
                        f"Generate debate about {topic}:\n\n" + propulsion, 69
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
