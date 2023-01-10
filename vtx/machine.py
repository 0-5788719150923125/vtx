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
        remove = False
        redact = False
        output = "ERROR: Me Found."

        head.build_context(str(message.author.id) + ": " + message.content)

        if message.author == self.user:
            return

        if message.content == "load":
            remove = True
            head.load_model()
            await message.channel.send("INFO: Reloaded the model.")
            await message.delete()
            return
        elif message.content == "prep":
            remove = True
            try:
                await message.channel.send("INFO: Prepping data.")
                await i.ingest()
            except:
                print("something tasted strange")
            await message.channel.send("INFO: Scraping Reddit.")
            await i.read()
            await message.channel.send("INFO: Done.")
            await message.delete()
            return

        print(bcolors.OKGREEN + "head" + bcolors.ENDC)
        if "gen" in message.content:
            weight = 1
            remove = True
            output = await head.gen(530243004334604311)
            print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
        else:
            try:
                if len(message.mentions) > 0:
                    weight = random.randrange(0, 40, 1)
                    bias = int(message.mentions[0].id)
                    print(bcolors.WARNING + "WARN: agent" + bcolors.ENDC)
                    print(bias)
                else:
                    bias = random.randrange(100, 333, 1)
                    weight = random.randrange(0, 101, 1)
            except:
                print("wrong length")

            string = str(message.author.id) + ": " + message.content
            print(bcolors.FAIL + "dj ent" + bcolors.ENDC)
            output = await head.gen(weight)

        if str(message.channel.type) == "private":
            weight = random.randint(0, 36)

        print("weight is " + str(weight))
        if weight > 33:
            print(bcolors.WARNING + "ERROR: Too heavy." + bcolors.ENDC)
            print("...")
            print("..")
            print(bcolors.FAIL + "." + bcolors.ENDC)
            return

        print(bcolors.OKGREEN + "output" + bcolors.ENDC)
        try:

            if random.randrange(0, 101, 1) < redacted_chance:
                redact = True

            if redact == True:
                choices = ["[REDACTED]", "[CLASSIFIED]", "[CORRUPTED]"]
                output = random.choice(choices)

            if remove == True:
                try:
                    await message.delete()
                    print("clean")
                except:
                    print("dirty")

            print(output)

            print(bcolors.FAIL + "." + bcolors.ENDC)
            print(".")

            if weight > 33:
                print(bcolors.FAIL + "." + bcolors.ENDC)
            else:
                print(bcolors.OKGREEN + "." + bcolors.ENDC)
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
            print(
                bcolors.FAIL
                + "You should probably be sending this to a daemon API like luciferian.ink/?pen=republican"
                + bcolors.ENDC
            )


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
    print("channels:")
    for guild in client.guilds:
        print("=> " + guild.name)
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(token)
