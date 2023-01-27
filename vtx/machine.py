import os
import re
import json
import time
import math
import random
import asyncio
import discord
import head
import yaml
import praw, asyncpraw
import functools
import typing
import asyncio
import requests
import pprint
import secrets
from functools import reduce
from mergedeep import merge, Strategy
import lab.reddit
import lab.twitter
import lab.source
import threading

redacted_chance = 1
response_probability = 10


with open("/vtx/defaults.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        # pprint.pprint(config)
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

    await asyncio.sleep(66.666)
    print(str(len(tasks)) + " running tasks")
    await main(loop)


def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main(loop))


loop = asyncio.get_event_loop()
t = threading.Thread(None, loop_in_thread, args=(loop,))
t.start()


class Client(discord.Client):

    thinking = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print("I am alive...")
        if config["mode"]["test"] == True:
            return
        url = "http://ctx:9665/message"
        myobj = {"message": "I am alive...", "identifier": "src"}
        x = requests.post(url, json=myobj)
        head.ai = await head.load_model()
        for guild in client.guilds:
            print("=> " + guild.name)

    async def setup_hook(self) -> None:
        self.discord_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        if config["mode"]["test"] == True:
            return
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(30, 21600)
            await asyncio.sleep(delay)
            self.thinking = True
            try:
                channels = await get_all_channels()
                channel = random.choice(channels)
                messages = [
                    message
                    async for message in self.get_channel(channel.id).history(limit=10)
                ]
                context = [
                    ":>" + str(messages[8].author.id) + ": " + messages[8].content,
                    ":>" + str(messages[5].author.id) + ": " + messages[5].content,
                    ":>" + str(messages[3].author.id) + ": " + messages[3].content,
                    ":>" + str(messages[2].author.id) + ": " + messages[2].content,
                    ":>" + str(messages[1].author.id) + ": " + messages[1].content,
                    ":>" + str(messages[0].author.id) + ": " + messages[0].content,
                ]
                head.ai = await head.load_model("mind")

                recent_author_id = messages[random.randint(0, 9)].author.id

                if str(recent_author_id) == str(self.user.id):
                    print(bcolors.WARNING + "WARN: found myself" + bcolors.ENDC)
                    neurons = [
                        random.randint(1, 9),  # neuron
                        random.randint(0, 9),  # neura
                        random.randint(0, 9),  # neu ra
                    ]
                    weight = random.randint(100000000000000, 9999999999999999)
                    bias = (
                        str(neurons[0])
                        + str(neurons[1])
                        + str(neurons[2])
                        + str(weight)
                    )
                else:
                    bias = recent_author_id

                output = await head.gen(int(bias), context)

                print("=> output to " + channel.name)
                print(output)

                head.ai = await head.load_model()
                await channel.send(output)
                self.thinking = False
            except Exception as e:
                print(bcolors.FAIL + str(e) + bcolors.ENDC)
                print(bcolors.FAIL + "failed to concentrate" + bcolors.ENDC)

    # check every Discord message
    async def on_message(self, message):

        reply = True

        if config["mode"]["test"] == True:
            return

        bias = 0
        output = "ERROR: Me Found."

        # every message is added to local cache, for building prompt
        head.build_context(str(message.author.id) + ": " + message.content)

        # ignore messages from the bot
        if message.author == self.user:
            return

        # ignore messages if heavy processing is taking place
        if self.thinking == True:
            return

        # generate responses
        print(bcolors.OKGREEN + "head" + bcolors.ENDC)
        if "gen" in message.content:
            print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
            weight = 1
            bias = 530243004334604311
            reply = False
            try:
                if message.content == "gen":
                    await message.delete()
            except:
                pass
        else:
            weight = random.randint(0, 100)
            print(bcolors.FAIL + "dj ent" + bcolors.ENDC)
            # increase probability of a response if bot is mentioned
            if client.user.mentioned_in(message):
                print(bcolors.WARNING + "WARN: bot" + bcolors.ENDC)
                weight = random.randint(
                    0, response_probability + (response_probability / 2)
                )  ## 66%
                bias = int(message.mentions[0].id)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                print(bcolors.WARNING + "WARN: agent" + bcolors.ENDC)
                bias = int(message.mentions[0].id)

        # increase response probability in private channels
        if str(message.channel.type) == "private":
            weight = 1

        print("weight is " + str(weight))

        # check weight before generating a response
        if weight > response_probability:
            print(bcolors.WARNING + "ERROR: Too heavy." + bcolors.ENDC)
            print("...")
            print("..")
            print(bcolors.FAIL + "." + bcolors.ENDC)
            return

        # generate a response from context and bias
        print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
        output = await head.gen(bias)
        print(bcolors.OKGREEN + "output" + bcolors.ENDC)

        # make random redactions
        if random.randint(0, 100) <= redacted_chance:
            choices = ["[REDACTED]", "[CLASSIFIED]", "[CORRUPTED]"]
            output = random.choice(choices)

        # output to console
        print(output)
        print(bcolors.FAIL + "." + bcolors.ENDC)
        print(".")
        print(bcolors.OKGREEN + "." + bcolors.ENDC)
        print(bcolors.OKGREEN + "ok" + bcolors.ENDC)

        async with message.channel.typing():
            time.sleep(10)

        try:
            if reply == True:
                await message.reply(output)
            else:
                await message.channel.send(output)

        except:
            print(bcolors.FAIL + "Failed to send Discord message." + bcolors.ENDC)
            await message.reply("ERROR: Me Found.")


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# list all available Discord channels
async def get_all_channels():
    text_channel_list = []
    for guild in client.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


if "discord" in config:
    discord_token = os.environ["DISCORDTOKEN"]
    intents = discord.Intents.default()
    intents.message_content = True

    client = Client(intents=intents)
    client.run(discord_token)
