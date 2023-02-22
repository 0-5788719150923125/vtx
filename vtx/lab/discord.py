from utils import ad, bc, config, propulsion, ship
import asyncio
import discord
import random
import head
import os


redacted_chance = 1
response_probability = 10
followup_probability = 10


# A class to control the entire Discord bot
class Client(discord.Client):

    # A variable that will block all actions until True
    thinking = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # List all Discord servers on startup
        print(bc.ROOT + "ONE@ROOT: " + ad.TEXT + "connected to Discord")
        guilds = []
        for guild in client.guilds:
            guilds.append(guild.name)

        print(bc.FOLD + "PEN@DISCORD: " + ad.TEXT + " => ".join(guilds))

    async def setup_hook(self) -> None:
        self.discord_task = self.loop.create_task(self.think())

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(3600, 21600)
            await asyncio.sleep(delay)
            self.thinking = True
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

        # every message is added to local cache, for building prompt
        head.build_context(str(message.author.id) + ship + " " + message.content)

        # ignore messages if heavy processing is taking place
        if self.thinking == True:
            return

        # ignore messages from the bot
        if message.author == self.user:
            if random.randint(0, 100) <= followup_probability:
                response_probability == 100
            else:
                return

        # generate responses
        print(bc.ROOT + "head" + ad.TEXT)
        if "gen" in message.content:
            print(bc.FOLD + "dj ent" + ad.TEXT)
            weight = 1
            bias = 530243004334604311
            try:
                if message.content == "gen":
                    reply = False
                    await message.delete()
            except:
                pass
        else:
            weight = random.randint(0, 100)
            print(bc.FOLD + "heads" + ad.TEXT)
            # increase probability of a response if bot is mentioned
            if client.user.mentioned_in(message):
                weight = random.randint(
                    0, response_probability + (response_probability / 2)
                )  ## 66%
                bias = int(message.mentions[0].id)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
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
            print(bc.CORE + "..." + ad.TEXT)
            return

        # generate a response from context and bias
        print(bc.ROOT + "heads" + ad.TEXT)
        await asyncio.sleep(random.randint(2, 13))
        async with message.channel.typing():
            generation = await head.gen(bias)
            output = transformer([generation[0], generation[1]])

        print(bc.FOLD + "output" + ad.TEXT)

        # make random redactions
        if random.randint(0, 100) <= redacted_chance:
            choices = ["[REDACTED]", "[CLASSIFIED]", "[CORRUPTED]"]
            output = random.choice(choices)

        # output to console
        print(output)
        print(bc.CORE + "..." + ad.TEXT)
        await asyncio.sleep(1)
        print("..")
        await asyncio.sleep(0.5)
        print(bc.ROOT + "." + ad.TEXT)
        await asyncio.sleep(2)
        print(bc.ROOT + "ok" + ad.TEXT)

        try:
            if len(output) > 2000:
                output = output[:1997] + "..."
            if reply == True:
                await message.reply(output)
            else:
                await message.channel.send(output)
        except:
            print(bc.CORE + "Failed to send Discord message." + ad.TEXT)
            error = "".join(random.choices(list(bullets), k=random.randint(42, 128)))
            await message.channel.send(error)


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
async def subscribe():
    if "discord" in config:
        await client.start(discord_token)


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
