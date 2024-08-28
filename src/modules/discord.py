import asyncio
import base64
import io
import logging
import os
import random
import time
import math
import re
import threading
from pprint import pprint

import discord
import requests
from cerberus import Validator
from discord import Permissions, app_commands

import head
from common import analyze_images, bullets, colors, get_identity, ship, wall
from events import consumer, producer


def main(config):
    if config["discord"] is None:
        config["discord"] = {}
    result = validation(config["discord"])
    if not result:
        return
    asyncio.run(run_client(config))


if __name__ == "__main__":
    main(config)


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
    intents.typing = True
    intents.presences = True
    intents.guilds = True

    client = Client(intents=intents, config=config)

    await asyncio.gather(subscribe_events(config), client.start(discord_token))


def validation(config):
    schema = {
        "use_self_token": {"type": "boolean"},
        "export_dms": {"type": "boolean"},
        "debug": {"type": "boolean"},
        "frequency": {"type": "float"},
        "max_frequency": {"type": "float"},
        "decay_rate": {"type": "float"},
        "reply_frequency": {"type": "float"},
        "mention_self_frequency": {"type": "float"},
        "mention_any_frequency": {"type": "float"},
        "bannedUsers": {"type": "list"},
        "bannedServers": {"type": "list"},
        "horde_enabled": {"type": "boolean"},
        "musing": {"type": "list"},
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


async def subscribe_events(config):
    servers = config["discord"].get("servers", {})
    if len(servers) == 0:
        return
    while True:
        await asyncio.sleep(6.66)
        item = consumer("new_reddit_submission")
        if not item:
            continue
        for server in servers:
            data = servers.get(server)
            if data is None:
                continue
            webhook_url = data.get("webhook")
            if webhook_url is None:
                continue
            allowed_tags = data.get("tags", [])
            for tag in item.get("tags", []):
                if tag in allowed_tags:
                    send_webhook(
                        webhook_url=webhook_url,
                        title=item["title"],
                        link=item["link"],
                        avatar_url=data.get("avatar", item["avatar_url"]),
                        username=data.get("author", item["username"]),
                        thumbnail=data.get("logo", item["thumbnail"]),
                        description=item["description"],
                        footer=item["footer"],
                        content=f"Event: new_reddit_submission",
                    )
                    break


# A class to control the entire Discord bot
class Client(discord.Client):
    def __init__(self, *args, **kwargs):
        self.config = kwargs["config"]
        self.ignoring = {}
        self.last_response_times = {}
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        # Register slash commands
        try:
            tree = app_commands.CommandTree(self)

            @tree.command(name="echo", description="Say something.")
            @app_commands.default_permissions(administrator=True)
            async def echo_command(interaction, message: str):
                await interaction.response.send_message(
                    "Message sent.",
                    ephemeral=True,
                    delete_after=60,
                )
                await interaction.channel.send(message)

            if self.config["discord"].get("horde_enabled", False):

                @tree.command(name="x", description="Plant a seed.")
                async def x_command(interaction):
                    message = await interaction.response.send_message(
                        "Allow me to create something for you.",
                        ephemeral=True,
                        delete_after=3600,
                    )
                    producer(
                        {
                            "event": "generate_image",
                            "source": "discord",
                            "channel_id": interaction.channel.id,
                        },
                    )

            await tree.sync()
        except Exception as e:
            print(e)

        # List all Discord servers on startup
        guilds = []
        for guild in sorted(
            self.guilds, key=lambda guild: guild.member_count, reverse=True
        ):
            banned = await self.check_bans(guild=guild)
            if banned:
                continue

            guilds.append(f"{guild.name} ({guild.member_count})")
        print(colors.BLUE + "ONE@DISCORD: " + colors.WHITE + " => ".join(guilds))

        self.brain = self.loop.create_task(self.start_musing())

    async def on_guild_join(self, guild):
        await self.check_bans(guild=guild)

    async def check_bans(self, guild=None, user=None) -> bool:
        if guild is not None:
            if int(guild.id) in self.config["discord"].get("bannedServers", []):
                print(f"leaving: {guild.name}")
                await guild.leave()
                return True

        if user is not None:
            if int(user.id) in self.config["discord"].get("bannedusers", []):
                return True

        return False

    async def setup_hook(self) -> None:
        self.responder = self.loop.create_task(self.respond_to_things())

    async def respond_to_things(self) -> None:
        try:
            while True:
                await asyncio.sleep(6.66)
                item = consumer("publish_image")
                if item:
                    file = discord.File(
                        io.BytesIO(base64.b64decode(item["response"])),
                        filename="nft.webp",
                    )
                    channel = self.get_channel(item["channel_id"])
                    await channel.send(file=file)
        except Exception as e:
            logging.error(e)

    def should_ignore(self, target="global"):
        self.ignoring[target] = True

    def should_not_ignore(self, target="global"):
        self.ignoring[target] = False

    def is_ignoring(self, target="global"):
        return self.ignoring.get(target, False)

    # randomly generate commentary
    async def start_musing(self):
        musings = self.config["discord"]["musing"]
        while True:
            delay = random.randint(60, 66)
            await asyncio.sleep(delay)
            for choice in musings:
                try:
                    frequency = choice.get("frequency", 0)

                    if random.random() > frequency:
                        continue

                    self.should_ignore()

                    persona = choice.get("persona")
                    instruction = choice.get("instruction")
                    prompt = random.choice(choice.get("prompts"))
                    channel = self.get_channel(random.choice(choice.get("channels")))

                    ctx = [{"bias": 806051627198709760, "message": instruction}]
                    iterations = random.randrange(6, 9)
                    for i in range(iterations):
                        await asyncio.sleep(random.randint(9, 18))
                        async with channel.typing():
                            success, bias, output, seeded = await head.ctx.chat(
                                ctx=ctx,
                                personas=persona,
                                start_with=prompt,
                                priority=True,
                                max_new_tokens=333,
                            )
                            if not success:
                                continue
                            prompt = None
                            await channel.send(output)
                            head.ctx.build_context(bias=int(bias), message=output)
                            ctx.append({"bias": bias, "message": output})
                            print(colors.RED + "ONE@DISCORD: " + colors.WHITE + output)

                except Exception as e:
                    logging.error(e)

            self.should_not_ignore()

    async def send_dm(self, bias):
        user = self.get_user(bias)
        message = random.choice(
            [
                "Pardon, are you busy?",
                "Hey, do you have a minute?",
                "Can I ask you a question?",
                "Would you help me with something?",
            ]
        )
        if user:
            await user.send(message)
            print(colors.RED + "ONE@DISCORD: " + colors.WHITE + "DM: " + message)

    def mentioned_me(self, message):
        try:
            normalized = message.content.lower()
            if (
                self.user.display_name.lower() in normalized
                or message.guild.me.nick.lower() in normalized
            ):
                return True
            else:
                return False
        except:
            return False

    def calculate_frequency(
        self, time_elapsed, max_frequency, min_frequency, decay_rate
    ):
        # Calculate the decayed frequency
        decayed_frequency = max_frequency * math.exp(-decay_rate * time_elapsed)

        # Ensure the frequency doesn't fall below the baseline
        return max(decayed_frequency, min_frequency)

    # check every Discord message
    async def on_message(self, message):
        banned = await self.check_bans(guild=message.guild, user=message.author)
        if banned:
            return

        reply_frequency = self.config["discord"].get("reply_frequency", 0.333)
        reply = lambda weights: random.choices(
            [True, False], weights=[reply_frequency, 1.0 - reply_frequency], k=1
        )[0]

        if (
            message.author == self.user
            or message.content[:1] in bullets
            or message.content == ""
            and len(message.attachments) < 1
        ):
            return

        bias = None
        transformed = "ERROR: Me Found."
        roll = random.random()

        min_frequency = self.config["discord"].get("frequency", 0.01)
        max_frequency = self.config["discord"].get("max_frequency", 0.5)
        decay_rate = self.config["discord"].get("decay_rate", 0.1)

        current_time = time.time()
        last_response_time = current_time - self.last_response_times.get(
            message.channel.id, 0
        )

        frequency = self.calculate_frequency(
            last_response_time, max_frequency, min_frequency, decay_rate
        )

        mention_self_frequency = self.config["discord"].get(
            "mention_self_frequency", 0.88
        )
        mention_any_frequency = self.config["discord"].get(
            "mention_any_frequency", 0.08
        )

        # every message is added to local cache, for building prompt
        if message.content.lower() != "gen" and message.author != self.user:
            author_id = str(message.author.id)
            if str(message.channel.type) == "private":
                log_private_message(
                    author_id, wall + author_id + ship + " " + message.content
                )
                author_id = author_id[::-1]
            head.ctx.build_context(bias=int(author_id), message=message.content)

        urls = []
        watched = ["imgur.com", ".png", ".jpg", ".jpeg", ".gif", ".webp"]
        for embed in message.embeds:
            for seq in watched:
                if seq in embed.url.lower():
                    urls.append(embed.url)

        if len(message.attachments) > 0:
            for attachment in message.attachments:
                urls.append(attachment.url)

        if len(urls) > 0:
            preds = await analyze_images(urls)
            pred = f"(This image appears to be: {', '.join(preds)})"
            head.ctx.build_context(bias=int(self.user.id), message=pred)
            print(colors.GREEN + "ONE@DISCORD: " + colors.WHITE + pred)

        if self.is_ignoring(message.channel.id):
            return

        # We need to place all of the following logic into a dedicated function. We need to
        # check the incoming message for a URL, and if it exists, we need to return. We need
        # to watch the on_message_edit event, and continue the function after it fires. The
        # reason is, embeds are not available here. The on_message_edit event will fire after
        # this one, and it will contain embed information, like title and description.

        # sanitized = re.sub(
        #     r"http\S+",
        #     "<|url|>",
        #     string,
        # )
        # if message.embeds:
        #     print("Truuuu")
        # for embed in message.embeds:
        #     if embed.type == "rich":
        #         message.content = (
        #             f"{message.content} | {embed.title} | {embed.description}"
        #         )

        if message.content != "":
            print(colors.BLUE + "ONE@DISCORD: " + colors.WHITE + message.content)

        # generate responses
        if "gen" in message.content.lower():
            roll = 0  # Always
            bias = 530243004334604311
            try:
                if message.content == "gen":
                    reply = False
                    await message.delete()
            except:
                pass
        elif self.mentioned_me(message):
            roll = 0
        else:
            # increase probability of a response if bot is mentioned
            if self.user.mentioned_in(message):
                frequency = max(mention_self_frequency, frequency)
            # if a user is mentioned, attempt to respond as them
            elif len(message.mentions) > 0:
                frequency = max(mention_any_frequency, frequency)
                bias = int(message.mentions[0].id)

        # increase response probability in private channels
        no_transform = False
        if str(message.channel.type) == "private":
            # if a user is mentioned in private, send a message to them
            group = re.search(r"(?:[<][@])(\d{18,19})(?:[>])", message.content)
            if group is not None and group[1] is not None:
                bias = group[1]
                await self.send_dm(bias=int(bias))
                return
            roll = 0  # Always
            bias = message.author.id
            no_transform = True
            reply = False

        if self.config["discord"].get("debug", False):
            if message.guild is not None:
                print(f"Guild: {message.guild.id}")
            print(f"Sender: {message.author.id}")
            print(f"Time elapsed: {last_response_time:.2f}s")
            print(f"Current frequency: {frequency:.4f}")
            print(f"Roll: {roll:.4f}")
            print(f"Will respond: {roll < frequency}")
            print("--------------------")

        # check frequency before generating a response
        if roll > frequency:
            return

        self.should_ignore(message.channel.id)

        # generate a response from context and bias
        await asyncio.sleep(random.randint(2, 13))
        try:
            async with message.channel.typing():
                persona = []
                if message.guild and int(message.guild.id) in self.config[
                    "discord"
                ].get("servers", {}):
                    server = self.config["discord"]["servers"][int(message.guild.id)]
                    if server is not None:
                        if "persona" in server:
                            persona = server.get("persona")
                            no_transform = True

                if len(message.mentions) > 0 and not self.user.mentioned_in(message):
                    no_transform = False
                    persona = []

                success, bias, output, seeded = await head.ctx.chat(
                    bias=bias, personas=persona, priority=True, max_new_tokens=333
                )

                if output == False:
                    return
                if no_transform:
                    transformed = output
                else:
                    transformed = transformer(bias, output)

            if len(transformed) > 2000:
                transformed = transformed[:1997] + "..."

            print(colors.RED + "ONE@DISCORD: " + colors.WHITE + transformed)

            if reply == True:
                return_message = await message.reply(transformed)
            else:
                return_message = await message.channel.send(transformed)

            bot_id = str(self.user.id)

            if str(message.channel.type) == "private":
                bot_id = str(bias)
                log_private_message(
                    str(bias),
                    wall + str(return_message.id) + ship + " " + transformed,
                )

            head.ctx.build_context(bias=int(bot_id), message=output)

            self.last_response_times[message.channel.id] = time.time()

        except Exception as e:
            print(e)
            import traceback

            print(traceback.format_exc())

        self.should_not_ignore(message.channel.id)

    # Handle bots that update messages token-by-token
    async def on_message_edit(self, before, after):
        if after.content[:1] not in bullets and before.content != after.content:
            if after.author.id != self.user.id:
                head.ctx.build_context(bias=int(after.author.id), message=after.content)
                print(colors.BLUE + "ONE@DISCORD: " + colors.WHITE + after.content)
            else:
                print(colors.RED + "ONE@DISCORD: " + colors.WHITE + after.content)

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
                server = None
                if reaction.message.guild is not None:
                    server = (
                        self.config["discord"]
                        .get("servers", {})
                        .get(int(reaction.message.guild.id), None)
                    )
                bias = None
                persona = []
                if server is not None:
                    if "persona" in server:
                        persona = server.get("persona", [])
                        no_transform = True
                i = length
                while i > 0:
                    i = i - 1
                    context.append(
                        {
                            "bias": int(messages[i].author.id),
                            "message": messages[i].content,
                        }
                    )
                if str(message.channel.type) == "private":
                    bias = int(self.user.id)
                    success, bias, output, seeded = await head.ctx.chat(
                        bias=bias,
                        personas=persona,
                        ctx=context,
                        priority=True,
                        max_new_tokens=333,
                    )
                    if success == False:
                        return
                    head.ctx.edit_message(message.content, output)
                    # replace_private_message(
                    #     str(self.user.id),
                    #     str(reaction.message.id),
                    #     wall + str(reaction.message.id) + ship + " " + output,
                    # )
                    transformed = output
                else:
                    success, bias, output, seeded = await head.ctx.chat(
                        bias=bias,
                        personas=persona,
                        ctx=context,
                        priority=True,
                        max_new_tokens=333,
                    )
                    if success == False:
                        return
                    head.ctx.edit_message(message.content, output)
                    if no_transform:
                        transformed = output
                    else:
                        transformed = transformer(bias, output)

                await message.edit(content=transformed)
            except Exception as e:
                logging.error(e)
                import traceback

                print(traceback.format_exc())


# format the output
def transformer(bias, text):
    responses = [
        f'The clone of <@{bias}> suggests, *"{text}"*',
        f'<@{bias}> says, *"{text}"*',
        f'<@{bias}> would say, *"{text}"*',
        f'They said, *"{text}"*',
        f"{text}",
    ]
    return random.choice(responses)


# Log private messages
def log_private_message(user_id, message):
    if not os.path.exists("/lab/discord/private"):
        os.makedirs("/lab/discord/private")

    with open("/lab/discord/private/" + user_id + ".txt", "a") as txt_file:
        sanitized = re.sub(
            r"http\S+",
            f"((({str(get_identity())})))",
            message,
        )
        txt_file.write(sanitized + "\n")


# Replace a private message
def replace_private_message(user_id, message_id, message):
    # Open the input and output files
    user_log = "/lab/discord/private/" + user_id
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
):
    data = {
        "username": username,
        "avatar_url": avatar_url,
        "content": content,
        "embeds": [
            {
                "title": title,
                "description": (
                    str(description)[:333] + "..."
                    if len(description) > 333
                    else description
                ),
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
