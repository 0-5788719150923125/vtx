import os
import re
import json
import time
import random
import asyncio
import discord
import i
import head

token = os.environ["DISCORDTOKEN"]


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
            delay = random.randrange(10, 3600, 1)
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

        head.add_context(str(message.author.id) + ": " + message.content)

        if message.author == self.user:
            return

        if message.content == "load":
            head.load_model()
            await message.channel.send("INFO: Reloaded the model.")
            return
        elif message.content == "prep":
            try:
                await message.channel.send("INFO: Prepping data.")
                await i.feed()
            except:
                print("something tasted strange")
            await message.channel.send("INFO: Scraping Reddit.")
            await i.scrape()
            await message.channel.send("INFO: Done.")
            return

        print(bcolors.OKGREEN + "head" + bcolors.ENDC)
        if "gen" in message.content:
            weight = 1
            output = await head.gen(530243004334604311)
            remove = True
            redact = False
            print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
        else:
            bias = random.randrange(100, 333, 1)
            weight = random.randrange(0, 101, 1)
            string = str(message.author.id) + ": " + message.content
            print(bcolors.FAIL + "dj ent" + bcolors.ENDC)
            await save_message(string)
            print(string)
            output = await head.gen(weight)

        try:
            if len(message.mentions) > 0:
                weight = 33
                bias = int(message.mentions[0].id)
                print(bcolors.WARNING + "WARN: agent" + bcolors.ENDC)
                print(bias)
        except:
            print("wrong length")

        if str(message.channel.type) == "private":
            weight = random.randint(0, 36)

        print("weight is " + str(weight))
        if weight > 33:
            print(bcolors.WARNING + "ERROR: Too heavy." + bcolors.ENDC)
            print("...")
            print("..")
            print(bcolors.FAIL + "." + bcolors.ENDC)
            return

        print("output")
        try:
            if redact == True:
                output = "[REDACTED]"

            if remove == True:
                try:
                    await message.delete()
                    print("clean")
                except:
                    output = await head.gen(bias)
                    print("dirty")

            print(output)

            print(bcolors.FAIL + "." + bcolors.ENDC)
            print(".")

            if weight > 33:
                print(bcolors.FAIL + "." + bcolors.ENDC)
            else:
                print(bcolors.OKGREEN + "." + bcolors.ENDC)
            print(bcolors.OKGREEN + "ok" + bcolors.ENDC)

            await save_message(output)
        except Exception as e:
            print(message.content)
            print(output)
            print(e)
            print(bcolors.FAIL + "ERROR: Me Found." + bcolors.ENDC)
        async with message.channel.typing():
            time.sleep(10)
        try:
            await message.channel.send(output)
        except:
            print(bcolors.FAIL + "Failed to send message to Discord." + bcolors.ENDC)
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


async def save_message(output):
    txt = open("./input.txt", "a")
    txt.write(f"{output}\n".format(output))
    txt.close()


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
