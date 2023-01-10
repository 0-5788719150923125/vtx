import os
import re
import json
import time
import random
import asyncio
import discord
import head
import i

token = os.environ["DISCORDTOKEN"]

redacted_chance = 1
response_probability = 33


class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print("I am alive...")

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randrange(10, 10800, 1)
            await asyncio.sleep(delay)
            neurons = [
                random.randint(0, 9),  # neuron
                random.randint(0, 9),  # neura
                random.randint(0, 9),  # neu ra
            ]
            bias = int(str(neurons[0]) + str(neurons[1]) + str(neurons[2]))
            print("my bias is " + str(bias))
            channels = await get_all_channels()
            channel = random.choice(channels)
            output = await head.gen(bias)
            print("=> output to " + channel.name)
            print(output)
            await channel.send(output)

    # check every Discord message
    async def on_message(self, message):
        bias = 0
        output = "ERROR: Me Found."

        # listen for commands
        if message.content == "load":
            head.load_model()
            await message.channel.send("INFO: Reloaded the model.")
            await message.delete()
            return
        elif message.content == "prep":
            await message.channel.send("INFO: Prepping Discord data.")
            await i.ingest()
            await message.channel.send("INFO: Scraping Reddit.")
            await i.read()
            await message.channel.send("INFO: Done.")
            await message.delete()
            return

        # every message is added to local cache, for building prompt
        head.build_context(str(message.author.id) + ": " + message.content)

        # ignore messages from the bot
        if message.author == self.user:
            return

        # generate responses
        print(bcolors.OKGREEN + "head" + bcolors.ENDC)
        if "gen" in message.content:
            print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
            weight = 1
            bias = 530243004334604311
            await message.delete()
        else:
            print(bcolors.FAIL + "dj ent" + bcolors.ENDC)
            # increase probability of a response if bot is mentioned
            if client.user.mentioned_in(message):
                weight = random.randint(0, 40)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                print(bcolors.WARNING + "WARN: agent" + bcolors.ENDC)
                print(bias)
                bias = int(message.mentions[0].id)
                weight = random.randint(0, 40)

            else:
                bias = random.randint(100, 999)
                weight = random.randint(0, 101)

        # increase response probability in private channels
        if str(message.channel.type) == "private":
            weight = random.randint(0, 36)

        print("weight is " + str(weight))
        status_color = bcolors.OKGREEN

        # check weight before generating a response
        if weight > response_probability:
            print(bcolors.WARNING + "ERROR: Too heavy." + bcolors.ENDC)
            print("...")
            print("..")
            print(bcolors.FAIL + "." + bcolors.ENDC)
            return

        # generate a response from context and bias
        output = await head.gen(bias)
        print(bcolors.OKGREEN + "output" + bcolors.ENDC)

        try:
            # make random redactions
            if random.randint(0, 101) <= redacted_chance:
                choices = ["[REDACTED]", "[CLASSIFIED]", "[CORRUPTED]"]
                output = random.choice(choices)

            # output to console
            print(output)
            print(bcolors.FAIL + "." + bcolors.ENDC)
            print(".")
            print(status_color + "." + bcolors.ENDC)
            print(bcolors.OKGREEN + "ok" + bcolors.ENDC)
        except Exception as e:
            print(message.content)
            print(output)
            print(bcolors.FAIL + e + bcolors.ENDC)
        async with message.channel.typing():
            time.sleep(10)
        try:
            await message.channel.send(output)
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


async def get_all_channels():
    text_channel_list = []
    for guild in client.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(token)
