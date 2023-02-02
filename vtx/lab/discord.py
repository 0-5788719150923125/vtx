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
import threading

redacted_chance = 1
response_probability = 10


with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

propulsion = "¶"
ship = ":>"


# A class to control the entire Discord bot
class Client(discord.Client):

    # A variable that will block all actions until True
    thinking = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print("I am alive...")

        # Load the AI model at startup
        head.ai = await head.load_model()

        # List all Discord servers on startup
        for guild in client.guilds:
            print("=> " + guild.name)

    async def setup_hook(self) -> None:
        self.discord_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(30, 10800)
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
                    propulsion
                    + str(messages[8].author.id)
                    + ship
                    + " "
                    + messages[8].content,
                    propulsion
                    + str(messages[5].author.id)
                    + ship
                    + messages[5].content,
                    propulsion
                    + str(messages[3].author.id)
                    + ship
                    + messages[3].content,
                    propulsion
                    + str(messages[2].author.id)
                    + ship
                    + messages[2].content,
                    propulsion
                    + str(messages[1].author.id)
                    + ship
                    + messages[1].content,
                    propulsion
                    + str(messages[0].author.id)
                    + ship
                    + messages[0].content,
                ]
                head.ai = await head.load_model("toe")

                recent_author_id = messages[random.randint(0, 9)].author.id

                if str(recent_author_id) == str(self.user.id):
                    print(bc.WARNING + "WARN: found myself" + bc.ENDC)
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
                print(bc.CORE + str(e) + bc.ENDC)
                print(bc.CORE + "failed to concentrate" + bc.ENDC)

    # check every Discord message
    async def on_message(self, message):

        reply = True

        bias = 0
        output = "ERROR: Me Found."

        # every message is added to local cache, for building prompt
        head.build_context(str(message.author.id) + ship + " " + message.content)

        # ignore messages from the bot
        if message.author == self.user:
            return

        # ignore messages if heavy processing is taking place
        if self.thinking == True:
            return

        # generate responses
        print(bc.ROOT + "head" + bc.ENDC)
        if "gen" in message.content:
            print(bc.ROOT + "heads" + bc.ENDC)
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
            print(bc.CORE + "dj ent" + bc.ENDC)
            # increase probability of a response if bot is mentioned
            if client.user.mentioned_in(message):
                weight = random.randint(
                    0, response_probability + (response_probability / 2)
                )  ## 66%
                bias = int(message.mentions[0].id)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                weight = random.randint(
                    0, response_probability + (response_probability / 3)
                )  ## 33%
                bias = int(message.mentions[0].id)

        # increase response probability in private channels
        if str(message.channel.type) == "private":
            weight = 1

        print(
            "weight is " + str(weight) + ", threshold is " + str(response_probability)
        )

        # check weight before generating a response
        if weight > response_probability:
            print(".")
            await asyncio.sleep(1)
            print("..")
            await asyncio.sleep(0.5)
            print(bc.CORE + "..." + bc.ENDC)
            return

        # generate a response from context and bias
        print(bc.ROOT + "heads" + bc.ENDC)
        await asyncio.sleep(random.randint(2, 13))
        async with message.channel.typing():
            output = await head.gen(bias)
        print(bc.ROOT + "output" + bc.ENDC)

        # make random redactions
        if random.randint(0, 100) <= redacted_chance:
            choices = ["[REDACTED]", "[CLASSIFIED]", "[CORRUPTED]"]
            output = random.choice(choices)

        # output to console
        print(output)
        print(bc.CORE + "..." + bc.ENDC)
        await asyncio.sleep(1)
        print("..")
        await asyncio.sleep(0.5)
        print(bc.ROOT + "." + bc.ENDC)
        await asyncio.sleep(2)
        print(bc.ROOT + "ok" + bc.ENDC)

        # async with message.channel.typing():
        #     time.sleep(10)

        try:
            if len(output) > 2000:
                output = output[:1997] + "..."
            if reply == True:
                await message.reply(output)
            else:
                await message.channel.send(output)

        except:
            print(bc.CORE + "Failed to send Discord message." + bc.ENDC)
            error = "".join(random.choices(list(bullets), k=random.randint(42, 128)))
            await message.channel.send(error)


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    WARNING = "\033[93m"
    CORE = "\033[91m"
    ENDC = "\033[0m"


# list all available Discord channels
async def get_all_channels():
    text_channel_list = []
    for guild in client.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


discord_token = os.environ["DISCORDTOKEN"]
intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)

# Subscribe to a Discord bot via token
def subscribe():
    if "discord" in config:
        client.run(discord_token)


bullets = {
    "⠠",
    "⠏",
    "⠲",
    "⠢",
    "⠐",
    "⠕",
    "⠥",
    "⠭",
    "⠞",
    "⠱",
    "⠟",
    "⠒",
    "⠇",
    "⠙",
    "⠮",
    "⠪",
    "⠑",
    "⠷",
    "⠿",
    "⠊",
    "⠂",
    "⠅",
    "⠡",
    "⠬",
    "⠝",
    "⠰",
    "⠽",
    "⠻",
    "⠧",
    "⠃",
    "⠼",
    "⠹",
    "⠌",
    "⠵",
    "⠄",
    "⠎",
    "⠫",
    "⠳",
    "⠯",
    "⠗",
    "⠉",
    "⠁",
    "⠛",
    "⠸",
    "⠋",
    "⠺",
    "⠔",
    "⠓",
    "⠜",
    "⠆",
    "⠍",
    " ",
    "\n",
}
