import asyncio
import random
import os
from utils import ad, bc, config, get_identity, propulsion, ship
from discord.ext import commands
import discord
import head

client = None
response_chance = 10  # out of 100
followup_chance = 10  # out of 100


# A class to control the entire Discord bot
class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # List all Discord servers on startup
        print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + "connected to Discord")
        guilds = []
        try:
            for guild in client.guilds:
                guilds.append(guild.name)
        except Exception as e:
            print(e)

        print(bc.FOLD + "PEN@DISCORD: " + ad.TEXT + " => ".join(guilds))

    async def setup_hook(self) -> None:
        self.discord_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(3600, 21600)
            await asyncio.sleep(delay)
            try:
                channels = await get_all_channels()
                channel = random.choice(channels)
                print("=> sending to " + channel.name)
                messages = [
                    message
                    async for message in self.get_channel(channel.id).history(limit=16)
                ]
                focus_on = random.randint(0, 7)
                context = [
                    propulsion
                    + str(messages[focus_on + 4].author.id)
                    + ship
                    + " "
                    + messages[focus_on + 4].content,
                    propulsion
                    + str(messages[focus_on + 3].author.id)
                    + ship
                    + " "
                    + messages[focus_on + 3].content,
                    propulsion
                    + str(messages[focus_on + 2].author.id)
                    + ship
                    + " "
                    + messages[focus_on + 2].content,
                    propulsion
                    + str(messages[focus_on + 1].author.id)
                    + ship
                    + " "
                    + messages[focus_on + 1].content,
                    propulsion
                    + str(messages[focus_on].author.id)
                    + ship
                    + " "
                    + messages[focus_on].content,
                ]

                recent_author_id = messages[random.randint(0, 15)].author.id

                if str(recent_author_id) == str(self.user.id):
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

                generation = await head.gen(int(bias), context)
                if generation[0] == "error":
                    output = generation[1]
                else:
                    output = transformer([generation[0], generation[1]])

                print(output)

                await messages[focus_on].reply(output)
                self.thinking = False
            except Exception as e:
                print(bc.CORE + str(e) + ad.TEXT)
                self.discord_task = self.loop.create_task(self.think())

    # check every Discord message
    async def on_message(self, message):

        reply = random.choice([True, False])

        bias = 0
        output = "ERROR: Me Found."

        if message.content[:1] in head.bullets or message.content == "":
            return

        # every message is added to local cache, for building prompt
        if message.content != "gen" and message.author != self.user:
            author_id = str(message.author.id)
            if str(message.channel.type) == "private":
                log_private_message(
                    author_id, propulsion + author_id + ship + " " + message.content
                )
                author_id = author_id[::-1]
            head.build_context(propulsion + author_id + ship + " " + message.content)
            print(bc.FOLD + "PEN@DISCORD: " + ad.TEXT + message.content)

        # ignore messages from the bot
        if message.author == self.user:
            if random.randint(0, 100) < followup_chance:
                if not str(message.channel.type) == "private":
                    chance = 1
                else:
                    return
            else:
                return

        # generate responses
        if "gen" in message.content:
            chance = 1
            bias = 530243004334604311
            try:
                if message.content == "gen":
                    reply = False
                    await message.delete()
            except:
                pass
        else:
            # increase probability of a response if bot is mentioned
            if client.user.mentioned_in(message):
                chance = random.randint(0, 15)  ## 66%
                bias = int(message.mentions[0].id)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                chance = random.randint(0, 60)  ## 22%
                bias = int(message.mentions[0].id)
            else:
                chance = random.randint(0, 100)

        # increase response probability in private channels
        no_transform = False
        if str(message.channel.type) == "private":
            chance = 1
            bias = message.author.id
            no_transform = True
            reply = False

        # check chance before generating a response
        if chance > response_chance:
            return

        # generate a response from context and bias
        await asyncio.sleep(random.randint(2, 13))
        try:
            async with message.channel.typing():
                generation = await head.gen(bias)
                if generation[0] == "error":
                    if random.randint(0, 100) < 2:
                        output = generation[1]
                    else:
                        return
                elif no_transform:
                    output = generation[1]
                else:
                    output = transformer([generation[0], generation[1]])
        except Exception as e:
            print(e)

        try:
            if len(output) > 2000:
                output = output[:1997] + "..."

            print(bc.CORE + "INK@DISCORD: " + ad.TEXT + output)

            if reply == True:
                await message.reply(output)
            else:
                await message.channel.send(output)

            bot_id = str(self.user.id)

            if str(message.channel.type) == "private":
                bot_id = str(bias)
                log_private_message(
                    str(bias),
                    propulsion + get_identity() + ship + " " + output,
                )

            head.build_context(propulsion + bot_id + ship + " " + output)
        except:
            print(bc.CORE + "Failed to send Discord message." + ad.TEXT)


# format the output
def transformer(group):
    responses = [
        f'The ghost of <@{group[0]}> suggests, *"{group[1]}"*',
        f'<@{group[0]}> says, *"{group[1]}"*',
        f'<@{group[0]}> would say, *"{group[1]}"*',
        f'They said, *"{group[1]}"*',
        f"{group[1]}",
    ]
    return random.choice(responses)


# Log private messages
def log_private_message(user_id, message):

    if not os.path.exists("/lab/discord-live"):
        os.makedirs("/lab/discord-live")

    with open("/lab/discord-live/" + user_id + ".txt", "a") as txt_file:
        txt_file.write(message + "\n")


# list all available Discord channels
async def get_all_channels():
    text_channel_list = []
    for guild in client.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


# Subscribe to a Discord bot via token
async def subscribe():

    discord_token = os.environ["DISCORDTOKEN"]
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True

    global client
    client = Client(intents=intents)

    # Handle bots that update messages token-by-token
    @client.event
    async def on_message_edit(before, after):
        if after.content[:1] not in head.bullets:
            head.build_context(
                propulsion + str(after.author.id) + ship + " " + after.content
            )
            print(bc.FOLD + "PEN@DISCORD: " + ad.TEXT + after.content)

    if "discord" in config:
        await client.start(discord_token)
