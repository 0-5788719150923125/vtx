import os
import re
import json
import time
import math
import random
import asyncio
import head
import yaml
import praw, asyncpraw
import functools
import typing
import asyncio
import requests
import pprint
from functools import reduce
from mergedeep import merge, Strategy
import secrets
import lab.reddit
import lab.twitter
import lab.source
import lab.discord

# import lab.petals
import threading


with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        pprint.pprint(config)
except:
    config = default_config


async def background_task():
    while True:
        print("Background task running")
        await asyncio.sleep(1)


tasks = []


@asyncio.coroutine
async def main(loop):
    tasks = []

    if "source" in config:
        for channel in config["source"]:
            if "watch" in config["source"][channel]:
                if config["source"][channel]["watch"] == True:
                    task = loop.create_task(lab.source.subscribe(channel))
                    tasks.append(task)

    if "reddit" in config:
        for subreddit in config["reddit"]:
            if "watch" in config["reddit"][subreddit]:
                if config["reddit"][subreddit]["watch"] == True:
                    task = loop.create_task(lab.reddit.subscribe(subreddit))
                    tasks.append(task)

    task = loop.create_task(lab.petals.subscribe())
    tasks.append(task)

    print(str(len(tasks)) + " running tasks")
    await asyncio.sleep(666.666)
    await main(loop)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))


loop = asyncio.get_event_loop()
t = threading.Thread(None, loop_in_thread, args=(loop,))
t.start()

if "discord" in config:
    asyncio.run(lab.discord.subscribe())
