import asyncio
import random
import os
import re
import requests
import logging
import discord
from pprint import pprint
from cerberus import Validator
import head
from events import subscribe_event
from utils import ad, bc, bullets, get_identity, propulsion, ship

response_frequency = 3  # out of 100
mention_self_frequency = 88  # out of 100
mention_any_frequency = 8  # out of 100


def main(config):
    result = validation(config["discord"])
    if not result:
        return
    subscribe_events(config)
    asyncio.run(run_client(config))


if __name__ == "main":
    main(config)


def validation(config):
    schema = {
        "use_self_token": {"type": "boolean"},
        "export_dms": {"type": "boolean"},
        "servers": {
            "type": "dict",
            "keysrules": {"type": "integer"},
            "valuesrules": {
                "type": "dict",
                "nullable": True,
                "schema": {
                    "persona": {"type": "string"},
                    "past": {"type": "string"},
                    "skip": {"type": "boolean"},
                    "after": {"type": "string"},
                    "before": {"type": "string"},
                    "subscribe": {"type": "list"},
                    "author": {"type": "string"},
                    "logo": {"type": "string"},
                    "avatar": {"type": "string"},
                    "webhook": {"type": "string"},
                    "link": {"type": "string"},
                    "tags": {"type": "list"},
                },
            },
        },
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


def subscribe_events(config):
    servers = config["discord"].get("servers")
    for server in servers:
        if not servers[server] or not servers[server].get("subscribe"):
            continue
        for event in servers[server].get("subscribe"):
            data = servers[server]
            try:
                subscribe_event(
                    event,
                    send_webhook,
                    webhook_url=data.get("webhook"),
                    content=f"Event: {event}",
                    allowed_tags=data.get("tags", None),
                    config=data,
                )
            except Exception as e:
                logging.error(e)


# A class to control the entire Discord bot
class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        self.config = kwargs["config"]
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # List all Discord servers on startup
        guilds = []
        for guild in sorted(
            self.guilds, key=lambda guild: guild.member_count, reverse=True
        ):
            guilds.append(f"{guild.name} ({guild.member_count})")

        print(bc.FOLD + "PEN@DISCORD: " + ad.TEXT + " => ".join(guilds))

    async def setup_hook(self) -> None:
        # self.discord_task = self.loop.create_task(self.think())
        pass

    # randomly generate commentary
    async def think(self):
        await self.wait_until_ready()
        while not self.is_closed():
            delay = random.randint(900, 86400)
            await asyncio.sleep(delay)
            try:
                channels = await get_all_channels(self)
                channel = random.choice(channels)
                messages = [
                    message
                    async for message in self.get_channel(channel.id).history(limit=16)
                ]
                focus_on = random.randint(0, 7)
                length = 7
                context = []
                i = length
                while i > 0:
                    i = i - 1
                    context.append(
                        propulsion
                        + str(messages[focus_on + i].author.id)
                        + ship
                        + " "
                        + messages[focus_on + i].content
                    )
                recent_author_id = messages[random.randint(0, 15)].author.id

                bias = None
                if str(recent_author_id) != str(self.user.id):
                    bias = recent_author_id

                output = await head.ctx.chat(bias, context)
                if output[0] == False:
                    return

                transformed = transformer([output[0], output[1]])

                await messages[focus_on].reply(transformed)

            except Exception as e:
                logging.error(e)
                self.discord_task = self.loop.create_task(self.think())

    # check every Discord message
    async def on_message(self, message):
        reply = random.choice([True, False])

        bias = None
        transformed = "ERROR: Me Found."
        roll = random.randint(0, 100)

        if (
            message.author == self.user
            or message.content[:1] in bullets
            or message.content == ""
        ):
            return

        # every message is added to local cache, for building prompt
        if message.content != "gen" and message.author != self.user:
            author_id = str(message.author.id)
            if str(message.channel.type) == "private":
                log_private_message(
                    author_id, propulsion + author_id + ship + " " + message.content
                )
                author_id = author_id[::-1]
            head.ctx.build_context(
                propulsion + author_id + ship + " " + message.content
            )
            print(bc.FOLD + "ONE@DISCORD: " + ad.TEXT + message.content)

        # generate responses
        if "gen" in message.content:
            roll = 1
            bias = 530243004334604311
            try:
                if message.content == "gen":
                    reply = False
                    await message.delete()
            except:
                pass
        else:
            # increase probability of a response if bot is mentioned
            if self.user.mentioned_in(message):
                if random.randint(0, 100) < mention_self_frequency:
                    roll = 1
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                if random.randint(0, 100) < mention_any_frequency:
                    roll = 1
                bias = int(message.mentions[0].id)

        # increase response probability in private channels
        no_transform = False
        if str(message.channel.type) == "private":
            roll = 1
            bias = message.author.id
            no_transform = True
            reply = False

        # check frequency before generating a response
        if roll > response_frequency:
            return

        # generate a response from context and bias
        await asyncio.sleep(random.randint(2, 13))
        try:
            async with message.channel.typing():
                prefix = None
                if (
                    message.guild
                    and int(message.guild.id) in self.config["discord"]["servers"]
                ):
                    server = self.config["discord"]["servers"][int(message.guild.id)]
                    if server is not None:
                        if "persona" in server:
                            persona = self.config["personas"].get(server.get("persona"))
                            bias = persona.get("bias")
                            prefix = persona.get("persona")
                            no_transform = True

                output = await head.ctx.chat(bias=bias, prefix=prefix)

                if output[0] == False:
                    return
                elif no_transform:
                    transformed = output[1]
                else:
                    transformed = transformer([output[0], output[1]])
        except Exception as e:
            logging.error(e)

        try:
            if len(transformed) > 2000:
                transformed = transformed[:1997] + "..."

            print(bc.CORE + "ONE@DISCORD: " + ad.TEXT + transformed)

            if reply == True:
                return_message = await message.reply(transformed)
            else:
                return_message = await message.channel.send(transformed)

            bot_id = str(self.user.id)

            if str(message.channel.type) == "private":
                bot_id = str(bias)
                log_private_message(
                    str(bias),
                    propulsion + str(return_message.id) + ship + " " + transformed,
                )

            head.ctx.build_context(propulsion + bot_id + ship + " " + output[1])
        except:
            print(bc.CORE + "Failed to send Discord message." + ad.TEXT)

    # Handle bots that update messages token-by-token
    async def on_message_edit(self, before, after):
        if after.content[:1] not in bullets:
            head.ctx.build_context(
                propulsion + str(after.author.id) + ship + " " + after.content
            )
            if after.author.id != self.user.id:
                print(bc.FOLD + "ONE@DISCORD: " + ad.TEXT + after.content)
            else:
                print(bc.CORE + "ONE@DISCORD: " + ad.TEXT + after.content)

    # Listen for reactions
    async def on_reaction_add(self, reaction, user):
        if reaction.message.author.id != self.user.id:
            return
        if str(reaction.emoji) == "🧠":
            try:
                channel = reaction.message.channel
                message = await channel.fetch_message(reaction.message.id)
                length = 9
                messages = [
                    message
                    async for message in channel.history(before=message, limit=length)
                ]
                context = []
                no_transform = False
                server = self.config["discord"]["servers"][
                    int(reaction.message.guild.id)
                ]
                if server is not None:
                    if "persona" in server:
                        persona = self.config["personas"].get(server.get("persona"))
                        bias = persona.get("bias")
                        prefix = persona.get("persona")
                        no_transform = True
                i = length
                while i > 0:
                    i = i - 1
                    context.append(
                        propulsion
                        + str(messages[i].author.id)
                        + ship
                        + " "
                        + messages[i].content
                    )
                if str(message.channel.type) == "private":
                    bias = str(self.user.id)
                    output = await head.ctx.chat(bias=bias, prefix=prefix, ctx=context)
                    if output[0] == False:
                        return
                    head.ctx.replace(
                        message.content, propulsion + bias + ship + " " + output[1]
                    )
                    replace_private_message(
                        str(self.user.id),
                        str(reaction.message.id),
                        propulsion + str(reaction.message.id) + ship + " " + output[1],
                    )
                    transformed = output[1]
                else:
                    output = await head.ctx.chat(ctx=context)
                    if output[0] == False:
                        return
                    head.ctx.replace(
                        message.content, propulsion + output[0] + ship + " " + output[1]
                    )
                    if no_transform:
                        transformed = output[1]
                    else:
                        transformed = transformer(output)

                await message.edit(content=transformed)
            except Exception as e:
                logging.error(e)


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
    if not os.path.exists("/lab/discord/live"):
        os.makedirs("/lab/discord/live")

    with open("/lab/discord/live/" + user_id + ".txt", "a") as txt_file:
        sanitized = re.sub(
            r"http\S+",
            f"((({str(get_identity())})))",
            message,
        )
        txt_file.write(sanitized + "\n")


# Replace a private message
def replace_private_message(user_id, message_id, message):
    # Open the input and output files
    user_log = "/lab/discord/live/" + user_id
    # Open the input and temporary files
    try:
        with open(user_log + ".txt", "r") as input_file, open(
            user_log + ".tmp.txt", "w"
        ) as temp_file:
            # Loop over each line in the input file
            for line in input_file:
                # Check if the line contains the ID we're looking for
                if message_id in line:
                    # If it does, replace the line with the new text
                    temp_file.write(message + "\n")
                else:
                    # If it doesn't, write the original line to the temporary file
                    temp_file.write(line)

        os.replace(user_log + ".tmp.txt", user_log + ".txt")
    except Exception as e:
        logging.error(e)


# list all available Discord channels
async def get_all_channels(self):
    text_channel_list = []
    for guild in self.guilds:
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages:
                text_channel_list.append(channel)
    return text_channel_list


# Subscribe to a Discord bot via token
async def run_client(config):
    discord_token = os.environ["DISCORDTOKEN"]
    if not discord_token:
        return
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    intents.message_content = True

    client = Client(intents=intents, config=config)

    await client.start(discord_token)


def send_webhook(
    webhook_url: str,
    title: str,
    link: str,
    username: str = "The Source",
    avatar_url: str = "https://cdn.discordapp.com/avatars/957758215075004416/1c79616ea084910675e5df259bea1cf5.webp",
    description: str = "",
    thumbnail: str = "https://styles.redditmedia.com/t5_2sqtn6/styles/communityIcon_xfdgcz8156751.png",
    footer: str = "/r/TheInk",
    content: str = "For immediate disclosure...",
    allowed_tags=None,
    tags=None,
    config=None,
):
    if allowed_tags and tags:
        allowed = False
        for tag in tags:
            if tag in allowed_tags:
                allowed = True
                break
        if not allowed:
            return

    if config:
        avatar_url = config.get("avatar", avatar_url)
        username = config.get("author", username)
        thumbnail = config.get("logo", thumbnail)

    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": content,
        "embeds": [
            {
                "title": title,
                "description": str(description)[:333] + "..."
                if len(description) > 333
                else description,
                "url": link,
                "thumbnail": {
                    "url": thumbnail,
                },
                "footer": {
                    "text": footer,
                },
            }
        ],
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        logging.error(response)
