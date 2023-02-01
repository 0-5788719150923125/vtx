import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random
import requests
import json
import head
import secrets
import pprint

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


# Check the local GUN API for new messages
async def subscribe(channel):

    chance = config["source"].get("chance", 33)

    roll = random.randint(0, 100)

    if roll >= chance:
        return

    deep = requests.get("http://ctx:9666/channel")
    state = json.loads(deep.text)
    print(bc.ROOT + "ONE@ROOT:" + bc.ENDC + " " + state)
    if random.randint(0, 100) <= config["source"][channel]["chance"]:
        bias = get_identity()
        print(bc.CORE + "INK@CORE:" + bc.ENDC + " firing bullet " + str(bias))
        context = [
            propulsion + str(bias) + ship + " I am a chat bot named Penny.",
            propulsion + str(bias) + ship + " " + state,
        ]
        url = "http://ctx:9666/message"
        print("responding to source........")
        message = await head.gen(int(bias), context)
        print("responding to source...........")
        myobj = {"message": message, "identifier": str(bias)}
        print("responding to source...............")
        x = requests.post(url, json=myobj, headers={"Connection": "close"})
        x.close()
        print("responding to source..................")
        pprint.pprint(myobj)
    deep.close()


# Generate a pseudo-identity, in the Discord ID format
def get_identity():
    count = secrets.choice([18, 19])
    identity = "".join(secrets.choice("0123456789") for i in range(count))
    return identity


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
