import random
import os
import threading
import re
from utils import ad, bc, get_daemon, get_identity, propulsion, ship
import asyncio
import asyncpraw
import time
import logging
import head
from pprint import pprint
from cerberus import Validator
from events import post_event, subscribe_event
from lab.discord import send_webhook


def orchestrate(config) -> None:
    result = validation(config["reddit"])
    if not result:
        return
    asyncio.run(client(config))


def validation(config):
    schema = {
        "enabled": {"type": "boolean"},
        "delay": {
            "type": "dict",
            "schema": {"min": {"type": "integer"}, "max": {"type": "integer"}},
        },
        "stalk": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "chance": {"type": "number"},
                    "stalker": {"type": "string"},
                    "min": {"type": "integer"},
                    "max": {"type": "integer"},
                },
            },
        },
        "replacers": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {"type": "integer"},
        },
        "subs": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "limit": {"type": "integer"},
                    "chance": {"type": "float"},
                    "persona": {"type": "string"},
                    "skip": {"type": "boolean"},
                    "alerts": {"type": "string"},
                    "type": {
                        "type": "string",
                        "allowed": ["top", "new"],
                    },
                    "filter": {"type": "list"},
                    "submissions": {"type": "list"},
                },
            },
        },
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


async def client(config):
    async with asyncpraw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent="u/" + os.environ["REDDITAGENT"],
        username=os.environ["REDDITAGENT"],
        password=os.environ["REDDITPASSWORD"],
    ) as reddit:
        try:
            await asyncio.gather(
                subscribe_comments(reddit, config),
                subscribe_submissions(reddit, config),
                submission(reddit, config),
                stalker(reddit, config),
                listener(reddit, config),
            )
        except Exception as e:
            logging.error(e)


async def listener(reddit, config) -> None:
    try:
        subscribe_event("kb_updated", manage_submission)
    except Exception as e:
        logging.error(e)


async def manage_submission(title, content):
    try:
        async with asyncpraw.Reddit(
            client_id=os.environ["REDDITCLIENT"],
            client_secret=os.environ["REDDITSECRET"],
            user_agent="u/" + os.environ["REDDITAGENT"],
            username=os.environ["REDDITAGENT"],
            password=os.environ["REDDITPASSWORD"],
        ) as reddit:
            try:
                subreddit = await reddit.subreddit("TheInk")
                edited = False
                async for submission in subreddit.search(
                    query=f"title:'{title}'", syntax="lucene"
                ):
                    try:
                        print(submission.title)
                        if submission.title == title:
                            await submission.edit(body=content)
                            await submission.mod.approve()
                            edited = True
                            break
                    except Exception as e:
                        logging.error(e)
                if not edited:
                    submission = await subreddit.submit(title=title, selftext=content)
                    await submission.load()
                    await submission.mod.approve()
                    post_event(
                        "new_reddit_submission",
                        title=submission.title,
                        description=submission.selftext,
                        link=submission.shortlink,
                    )
            except Exception as e:
                logging.error(e)
    except Exception as e:
        logging.error(e)


async def stalker(reddit, config):
    async def watch_submissions(reddit, config, user):
        redditor = await reddit.redditor(user)
        async for submission in redditor.stream.submissions(skip_existing=True):
            try:
                victim = config["reddit"]["stalk"].get(user)

                chance = victim.get("chance", 0.1)

                if random.random() > chance:
                    continue

                await submission.load()
                await submission.subreddit.load()

                op = get_identity(user)

                context = [
                    propulsion
                    + str(get_identity())
                    + ship
                    + " /r/"
                    + submission.subreddit.display_name,
                    propulsion + str(op) + ship + " " + submission.title,
                    propulsion + str(op) + ship + " " + submission.selftext,
                ]

                stalker = config["personas"].get(victim.get("stalker", None), None)
                bias = stalker.get("bias", None) if stalker else None
                prompt = (
                    stalker.get("persona")
                    if stalker
                    else "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."
                )

                generation = await head.ctx.chat(
                    ctx=context,
                    bias=bias,
                    prefix=prompt,
                    decay_after_length=66,
                )

                msg = (
                    submission.title[:66] + "..."
                    if len(submission.title) > 66
                    else submission.title
                )
                print(bc.FOLD + "PEN@REDDIT: " + ad.TEXT + msg)

                if generation[0] == False:
                    continue

                if stalker:
                    output = generation[1]
                else:
                    daemon = get_daemon(generation[0])
                    output = transformer([daemon, generation[1]])

                min_delay = victim.get("min", 300)
                max_delay = victim.get("max", 900)
                asyncio.create_task(
                    reply(
                        submission,
                        output,
                        {"min": min_delay, "max": max_delay, "seeded": generation[2]},
                    )
                )
            except Exception as e:
                logging.error(e)

    async def watch_comments(reddit, config, user):
        redditor = await reddit.redditor(user)
        async for comment in redditor.stream.comments(skip_existing=True):
            try:
                victim = config["reddit"]["stalk"].get(user)

                chance = victim.get("chance", 0.1)
                if random.random() > chance:
                    continue

                await comment.load()
                context = await build_context(comment=comment)

                stalker = config["personas"].get(victim.get("stalker", None), None)
                bias = stalker.get("bias", None) if stalker else None
                prompt = (
                    stalker.get("prompt")
                    if stalker
                    else "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."
                )

                generation = await head.ctx.chat(
                    ctx=context,
                    bias=bias,
                    prefix=prompt,
                    decay_after_length=66,
                )

                msg = (
                    comment.body[:66] + "..."
                    if len(comment.body) > 66
                    else comment.body
                )
                print(bc.FOLD + "PEN@REDDIT: " + ad.TEXT + msg)

                if generation[0] == False:
                    continue

                if stalker:
                    output = generation[1]
                else:
                    daemon = get_daemon(generation[0])
                    output = transformer([daemon, generation[1]])

                min_delay = victim.get("min", 300)
                max_delay = victim.get("max", 900)
                asyncio.create_task(
                    reply(
                        comment,
                        output,
                        {"min": min_delay, "max": max_delay, "seeded": generation[2]},
                    )
                )
            except Exception as e:
                logging.error(e)

    tasks = {}
    while True:
        for task in list(tasks):
            if tasks[task].done():
                tasks.pop(task)

        loop = asyncio.get_event_loop()

        for user in config["reddit"]["stalk"]:
            c = user + "-c"
            if c not in tasks:
                task = loop.create_task(watch_comments(reddit, config, user))
                task.name = c
                tasks[c] = task

            s = user + "-s"
            if s not in tasks:
                task = loop.create_task(watch_submissions(reddit, config, user))
                task.name = s
                tasks[s] = task

        await asyncio.sleep(66.6)

    asyncio.create_task(stalker(reddit, config))


# Create a submission.
async def submission(reddit, config):
    while True:
        try:
            await asyncio.sleep(60)
            if "TheInk" not in config["reddit"]["subs"]:
                continue
            servers = config["reddit"]["subs"]["TheInk"]["submissions"]
            for server in servers:
                if random.random() > server.get("frequency", 0.00059):
                    continue
                subreddit = await reddit.subreddit("TheInk")
                title = server.get("title", "On the 5th of September...")
                prompt = server.get("prompt", "On the 5th of September, 2024,")
                output = await head.ctx.prompt(
                    prompt=prompt,
                    max_new_tokens=2048,
                    decay_after_length=1024,
                    decay_factor=0.00000023,
                )
                if output[0] == False:
                    return
                submission = await subreddit.submit(title=title, selftext=output)
                await submission.mod.approve()
                await submission.load()
                await submission.author.load()
                subreddit = await reddit.subreddit(submission.subreddit.display_name)
                await subreddit.load()
                description = (
                    str(submission.selftext)[:666] + "..."
                    if len(submission.selftext) > 666
                    else submission.selftext
                )
                if server.get("simplify", False) == True:
                    description = None

                webhooks = server.get("alert")
                for webhook in webhooks:
                    send_webhook(
                        webhook_url=webhook,
                        simplify=False,
                        username="/u/" + server.get("author", submission.author.name),
                        avatar_url=server.get("avatar", submission.author.icon_img),
                        content="A new Reddit submission:",
                        title=submission.title,
                        link=submission.shortlink,
                        description=description,
                        thumbnail=server.get("logo", subreddit.community_icon),
                        footer="/r/" + subreddit.display_name,
                    )
        except Exception as e:
            logging.error(e)

    asyncio.create_task(submission(reddit, config))


async def subscribe_submissions(reddit, config):
    try:
        active = []
        for sub in config["reddit"]["subs"]:
            if "chance" in config["reddit"]["subs"][sub]:
                if config["reddit"]["subs"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "alerts" in config["reddit"]["subs"][submission.subreddit.display_name]:
                webhook = config["reddit"]["subs"][
                    submission.subreddit.display_name
                ].get("alerts")
                await submission.load()
                await submission.author.load()
                subreddit = await reddit.subreddit(submission.subreddit.display_name)
                await subreddit.load()
                send_webhook(
                    webhook_url=webhook,
                    username="/u/" + submission.author.name,
                    avatar_url=submission.author.icon_img,
                    content="A new Reddit submission:",
                    title=submission.title,
                    link=submission.shortlink,
                    description=str(submission.selftext)[:666] + "..."
                    if len(submission.selftext) > 666
                    else submission.selftext,
                    thumbnail=subreddit.community_icon,
                    footer="/r/" + subreddit.display_name,
                )

            chance = config["reddit"]["subs"][submission.subreddit.display_name].get(
                "chance", 0
            )

            if submission.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue
            if random.random() > chance:
                continue

            op = get_identity()

            bias = None
            prompt = "I carefully respond to a submission on Reddit."

            sub = config["reddit"]["subs"][submission.subreddit.display_name]
            if "persona" in sub:
                persona = config["personas"].get(sub["persona"])
                bias = persona.get("bias")
                prompt = persona.get("persona")

            if "filter" in sub:
                ignore = False
                for term in sub.get("filter"):
                    if (
                        term in submission.title.lower()
                        or term in submission.selftext.lower()
                    ):
                        ignore = True
                        break
                if ignore:
                    continue

            context = [
                propulsion
                + str(get_identity())
                + ship
                + " /r/"
                + submission.subreddit.display_name,
                propulsion + str(op) + ship + " " + submission.title,
                propulsion + str(op) + ship + " " + submission.selftext,
            ]
            generation = await head.ctx.chat(
                ctx=context,
                prefix=prompt,
                bias=bias,
                decay_after_length=66,
            )

            msg = (
                submission.title[:66] + "..."
                if len(submission.title) > 66
                else submission.title
            )
            print(bc.FOLD + "PEN@REDDIT: " + ad.TEXT + msg)

            if generation[0] == False:
                continue
            else:
                daemon = get_daemon(generation[0])
                if "persona" in sub:
                    output = generation[1]
                else:
                    output = transformer([daemon, generation[1]])

            min_delay = config["reddit"]["delay"].get("min", 300)
            max_delay = config["reddit"]["delay"].get("max", 300)

            asyncio.create_task(
                reply(
                    submission,
                    output,
                    {"min": min_delay, "max": max_delay, "seeded": generation[2]},
                )
            )

    except Exception as e:
        logging.error(e)

    asyncio.create_task(subscribe_submissions(reddit, config))


# Subscribe to a single subreddit.
async def subscribe_comments(reddit, config):
    try:
        active = []
        for sub in config["reddit"]["subs"]:
            if "chance" in config["reddit"]["subs"][sub]:
                if config["reddit"]["subs"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for comment in subreddits.stream.comments(skip_existing=True):
            parent = await comment.parent()
            await parent.load()

            chance = config["reddit"]["subs"][comment.subreddit.display_name].get(
                "chance", 0
            )

            roll = random.random()
            if parent.author == os.environ["REDDITAGENT"]:
                roll = roll / (len("ACTG") * 100)  # the optimal number of children
            if roll >= chance:
                continue

            await comment.load()
            if comment.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue

            context = await build_context(comment=comment)

            bias = None
            prompt = "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."

            sub = config["reddit"]["subs"][comment.subreddit.display_name]
            if "persona" in sub:
                persona = config["personas"].get(sub["persona"])
                bias = persona.get("bias")
                prompt = persona.get("persona")

            if "filter" in sub:
                ignore = False
                submission = await reddit.submission(comment.submission)
                for term in sub.get("filter"):
                    if (
                        term in submission.title.lower()
                        or term in submission.selftext.lower()
                        or term in comment.body.lower()
                    ):
                        ignore = True
                        break
                if ignore:
                    continue

            generation = await head.ctx.chat(
                ctx=context,
                prefix=prompt,
                decay_after_length=66,
            )

            msg = comment.body[:66] + "..." if len(comment.body) > 66 else comment.body
            print(bc.FOLD + "PEN@REDDIT: " + ad.TEXT + msg)

            if generation[0] == False:
                continue

            daemon = get_daemon(generation[0])
            if "persona" in sub:
                output = generation[1]
            else:
                output = transformer([daemon, generation[1]])

            min_delay = config["reddit"]["delay"].get("min", 300)
            max_delay = config["reddit"]["delay"].get("max", 300)

            asyncio.create_task(
                reply(
                    comment,
                    output,
                    {"min": min_delay, "max": max_delay, "seeded": generation[2]},
                )
            )

    except Exception as e:
        logging.error(e)

    asyncio.create_task(subscribe_comments(reddit, config))


async def reply(obj, message, config):
    try:
        await asyncio.sleep(
            random.randint(config.get("min", 300), config.get("max", 900))
        )
        await obj.reply(message)

        color = bc.CORE
        if config.get("seeded", False) == True:
            color = bc.ROOT

        print(color + "INK@REDDIT: " + ad.TEXT + message)
    except Exception as e:
        logging.error(e)


# Build context from a chain of comments.
async def build_context(comment):
    context = [propulsion + str(get_identity()) + ship + " " + str(comment.body)]
    parent = await comment.parent()
    await parent.load()
    while isinstance(parent, asyncpraw.models.Comment):
        await parent.refresh()
        context.insert(
            0, propulsion + str(get_identity()) + ship + " " + str(parent.body)
        )
        parent = await parent.parent()
        await parent.load()
    context.insert(
        0,
        propulsion
        + str(get_identity())
        + ship
        + " "
        + str(parent.title)
        + " => "
        + str(parent.selftext),
    )
    return context


# Format the output.
def transformer(group):
    pronoun = random.choice(["My", "A"])
    types = random.choice(["daemon", "friend", "robot"])
    verb = random.choice(["says", "said", "wants to say", "whispers", "thinks"])
    responses = [
        f'{pronoun} {types} {verb}, "{group[1]}"',
        f'Penny {verb}, "{group[1]}"',
        f'{group[0]} {verb}, "{group[1]}"',
        f"{group[1]}",
    ]
    return random.choice(responses)
