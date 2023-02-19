import os
import re
import json
import time
import math
import random
import head
import yaml
import functools
import typing
import asyncio
import requests
import pprint
from functools import reduce
from mergedeep import merge, Strategy
import secrets
import lab.reddit
import threading
import lab.source
import lab.discord

# import lab.twitter
# import lab.petals
# from crontab import CronTab

# cron = CronTab(user="crow")
# job = cron.new(command="echo hello_world")
# job.minute.every(1)
# cron.write()


with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        pprint.pprint(config)
except:
    config = default_config


tasks = []


# from transformers import ViTFeatureExtractor, ViTModel
# from PIL import Image

# url = "http://images.cocodataset.org/val2017/000000039769.jpg"
# image = Image.open(requests.get(url, stream=True).raw)

# feature_extractor = ViTFeatureExtractor.from_pretrained("facebook/dino-vitb16")
# model = ViTModel.from_pretrained("facebook/dino-vitb16")
# inputs = feature_extractor(images=image, return_tensors="pt")
# outputs = model(**inputs)
# last_hidden_states = outputs.last_hidden_state
# print(last_hidden_states)

# This is the main loop for the entire machine
@asyncio.coroutine
async def main(loop):

    # Get configs, create tasks, and append to task queue
    if "source" in config:
        for channel in config["source"]:
            if "watch" in config["source"][channel]:
                if config["source"][channel]["watch"] == True:
                    name = "source-" + channel
                    task = loop.create_task(lab.source.subscribe(channel))
                    task.set_name(name)
                    tasks.append(task)

    if "reddit" in config:
        for subreddit in config["reddit"]:
            if "watch" in config["reddit"][subreddit]:
                if config["reddit"][subreddit]["watch"] == True:
                    name = "reddit-" + subreddit
                    task = loop.create_task(lab.reddit.subscribe(subreddit))
                    task.set_name(name)
                    tasks.append(task)

    # asyncio.gather(*tasks)

    # task = loop.create_task(lab.petals.subscribe())
    # tasks.append(task)
    # pprint.pprint(tasks)
    # print(str(len(tasks)) + " running tasks")
    await asyncio.sleep(66.6666)
    await main(loop)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))


# Start the main loop in a thread
loop = asyncio.get_event_loop()
t = threading.Thread(None, loop_in_thread, args=(loop,), daemon=True)
t.start()

# Run blocking services
if "discord" in config:
    asyncio.run(lab.discord.subscribe())
