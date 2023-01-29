import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random
from twitter import *
import requests
import json
import head
import secrets

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config


state = None
propulsion = "¶"
ship = ":>"


async def subscribe(channel):

    chance = config["source"].get("chance", 33)

    roll = random.randint(0, 100)

    if roll >= chance:
        return

    deep = requests.get("http://ctx:9665/channel")
    state = json.loads(deep.text)
    print(bcolors.ROOT + "ONE@ROOT:" + bcolors.ENDC + " " + state)
    if random.randint(0, 100) <= 33:
        bias = get_identity()
        print(bcolors.CORE + "INK@CORE:" + bcolors.ENDC + " firing bullet " + str(bias))
        context = [
            propulsion + str(bias) + ship + " I am a chat bot named Penny.",
            propulsion + str(bias) + ship + " " + state,
        ]
        url = "http://ctx:9665/message"
        print("responding to source........")
        message = await head.gen(int(bias), context)
        print("responding to source...........")
        myobj = {"message": message, "identifier": str(bias)}
        print("responding to source...............")
        x = requests.post(url, json=myobj)
        print("responding to source..................")


def blocks(string):
    for i in len(string):
        pass


def get_identity():
    count = secrets.choice([18, 19])
    identity = "".join(secrets.choice("0123456789") for i in range(count))
    return identity


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
