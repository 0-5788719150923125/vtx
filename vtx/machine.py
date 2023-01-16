import os
import re
import json
import time
import random
import asyncio
import discord
import head

token = os.environ["DISCORDTOKEN"]

redacted_chance = 1
response_probability = 10


class Client(discord.Client):

    thinking = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        head.ai = await head.load_model()
        print("I am alive...")

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(300, 10800)
            await asyncio.sleep(delay)
            self.thinking = True
            neurons = [
                random.randint(0, 9),  # neuron
                random.randint(0, 9),  # neura
                random.randint(0, 9),  # neu ra
            ]
            bias = int(str(neurons[0]) + str(neurons[1]) + str(neurons[2]))
            print("my bias is " + str(bias))
            try:
                channels = await get_all_channels()
                channel = random.choice(channels)
                messages = [
                    message
                    async for message in self.get_channel(channel.id).history(limit=11)
                ]
                context = [
                    str(messages[10].author.id) + ": " + messages[10].content,
                    str(messages[5].author.id) + ": " + messages[5].content,
                    str(messages[4].author.id) + ": " + messages[4].content,
                    str(messages[3].author.id) + ": " + messages[3].content,
                    str(messages[2].author.id) + ": " + messages[2].content,
                    str(messages[1].author.id) + ": " + messages[1].content,
                    str(messages[0].author.id) + ": " + messages[0].content,
                ]
                head.ai = await head.load_model("eye")
                output = await head.gen(bias, context)
                print("=> output to " + channel.name)
                print(output)
                head.ai = await head.load_model()
                await channel.send(output)
                self.thinking = False
            except:
                pass

    # check every Discord message
    async def on_message(self, message):
        bias = 0
        output = "ERROR: Me Found."

        # listen for commands
        if message.content == "load":
            head.ai = await head.load_model()
            await message.channel.send("INFO: Reloaded the model.")
            await message.delete()
            return

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
            print(bcolors.FAIL + "dj ent" + bcolors.ENDC)
            # increase probability of a response if bot is mentioned
            if message.reference is not None:
                print("this was a reply")
                weight = random.randint(0, 101)
            elif client.user.mentioned_in(message):
                weight = random.randint(0, 40)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                print(bcolors.WARNING + "WARN: agent" + bcolors.ENDC)
                print(bias)
                bias = int(message.mentions[0].id)
                weight = random.randint(0, response_probability + 5)
            else:
                bias = random.randint(100, 999)
                weight = random.randint(0, 101)

        # increase response probability in private channels
        if str(message.channel.type) == "private":
            weight = random.randint(0, response_probability + 1)

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
        print(bcolors.OKGREEN + "heads" + bcolors.ENDC)
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
