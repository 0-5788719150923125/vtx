import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random
from twitter import *
import requests
import json

with open("/vtx/defaults.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        pprint.pprint(config)
except:
    config = default_config


state = None


async def subscribe(channel):
    deep = requests.get("http://ctx:9665/channel")
    state = json.loads(deep.text)
    print(bcolors.ROOT + "ONE@ROOT:" + bcolors.ENDC + " message = " + state)


def blocks(string):
    for i in len(string):
        pass


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    FOLD = "\033[96m"
    ROOT = "\033[92m"
    WARNING = "\033[93m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
