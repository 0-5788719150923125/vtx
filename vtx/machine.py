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
import praw
import functools
import typing
import asyncio
import requests

redacted_chance = 1
response_probability = 10

with open("/lab/config.yml", "r") as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)


reddit = praw.Reddit(
    client_id=os.environ["REDDITCLIENT"],
    client_secret=os.environ["REDDITSECRET"],
    user_agent="u/" + os.environ["REDDITAGENT"],
    username=os.environ["REDDITAGENT"],
    password=os.environ["REDDITPASSWORD"],
)


def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper


@to_thread
def watch_reddit():
    print("running reddit thing")
    watch = ["SubSimGPT2Interactive"]

    for entry in config["reddit"]:
        if "watch" not in entry:
            continue
        if entry["watch"] == True:
            watch.append(entry["sub"])

    subreddit = reddit.subreddit("+".join(watch))
    print(subreddit.display_name)
    for comment in subreddit.stream.comments(skip_existing=True):
        print(bcolors.OKGREEN + comment.submission.title + bcolors.ENDC)
        print(comment.parent_id)
        parent = comment.parent()
        if isinstance(parent, praw.models.Submission):
            print(bcolors.FAIL + "is a submission" + bcolors.ENDC)
            print("=> " + str(parent.author))
            print("=> " + str(parent.title))
            print("=> " + str(parent.selftext))
        else:
            parent.refresh()
        print("=> " + str(parent.author))
        print("=> " + str(parent.body))
        print("==> " + str(comment.author))
        print("==> " + str(comment.body))
        # comment.reply("test!!")


class Client(discord.Client):

    thinking = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        url = "http://ctx:9665/message"
        myobj = {"message": "I am alive...", "identifier": "src", "pubKey": None}
        x = requests.post(url, json=myobj)

        await watch_reddit()
        if config["mode"]["test"] == True:
            return
        head.ai = await head.load_model()
        for guild in client.guilds:
            print("=> " + guild.name)
        print("I am alive...")

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
                head.ai = await head.load_model("head")

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
            # await message.channel.send(output)
            await message.reply(output)
        except:
            print(bcolors.FAIL + "Failed to send Discord message." + bcolors.ENDC)


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
