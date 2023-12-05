import asyncio
import logging
import os
import random
import re
import threading
import time
import traceback
from copy import deepcopy
from pprint import pprint

import asyncpraw
import ray
from cerberus import Validator

import head
from common import colors, get_daemon, get_identity
from pipe import consumer, producer


def main(config) -> None:
    result = validation(config["reddit"])
    if not result:
        return
    asyncio.run(client(config))


if __name__ == "main":
    main(config)


def validation(config):
    schema = {
        "enabled": {"type": "boolean"},
        "filter": {"type": "list"},
        "followup_frequency": {"type": "float"},
        "delay": {
            "type": "dict",
            "nullable": True,
            "schema": {"min": {"type": "integer"}, "max": {"type": "integer"}},
        },
        "stalk": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "frequency": {"type": "number"},
                    "proximal_frequency": {"type": "number"},
                    "followup_frequency": {"type": "float"},
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
                "nullable": True,
                "schema": {
                    "limit": {"type": "integer"},
                    "frequency": {"type": "float"},
                    "followup_frequency": {"type": "float"},
                    "persona": {"type": "string"},
                    "skip": {"type": "boolean"},
                    "tags": {"type": "list"},
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
        await follow_victims(reddit, config["reddit"])
        await asyncio.gather(
            subscribe_comments(reddit, config),
            subscribe_submissions(reddit, config),
            stalker(reddit, config),
            manage_submissions(reddit, config),
            receive_events(),
        )


async def follow_victims(reddit, config):
    if config.get("stalk", None) is None:
        return
    for user in config["stalk"]:
        victim = config["stalk"].get(user)
        try:
            redditor = await reddit.redditor(user)
            async for comment in redditor.comments.new(limit=10):
                # Subscribe to my victim's subreddits
                # subreddit = await reddit.subreddit(comment.subreddit.display_name)
                # await subreddit.load()
                # print(subreddit.subscribers)
                if comment.subreddit.display_name not in config["subs"]:
                    frequency = victim.get("proximal_frequency", 0.0)
                    if frequency > 0:
                        config["subs"][comment.subreddit.display_name] = {
                            "frequency": frequency
                        }
        except:
            logging.error(f"Failed to stalk {user}. Was their account deleted?")


queued = []


async def receive_events():
    while True:
        await asyncio.sleep(6.66)
        item = consumer("book_updated")
        if item:
            queued.append(item)


my_tags = []


async def manage_submissions(reddit, config):
    global my_tags
    global queued
    subreddits = config["reddit"]["subs"]
    cache_miss = {}
    while True:
        try:
            await asyncio.sleep(6.66)
            if len(queued) == 0:
                continue
            item = queued.pop(0)
            title = item["title"]
            content = item["content"]

            if cache_miss.get(title, None) is None:
                cache_miss[title] = 0

            # This is such a stupid hack, because passing information through
            # multiple events is hard.
            my_tags = item["tags"]
            for name in subreddits:
                sub = subreddits.get(name)
                allowed = False
                if sub is None:
                    continue
                if "tags" in sub:
                    target = sub["tags"][0]
                    if target in my_tags:
                        allowed = True
                if not allowed:
                    continue
                # We submit to the first tag found
                subreddit = await reddit.subreddit(name)

                edited = False
                async for submission in subreddit.search(
                    query=f"title:'{title}'", syntax="lucene"
                ):
                    if submission.title == title:
                        await submission.edit(body=content)
                        await submission.mod.approve()
                        edited = True
                        cache_miss[title] = 0
                        break

                if not edited:
                    cache_miss[title] += 1
                    print(f"cache miss {cache_miss[title]}")
                    if cache_miss[title] <= 3:
                        continue
                    cache_miss[title] = 0
                    try:
                        submission = await subreddit.submit(
                            title=title, selftext=content
                        )
                        await submission.load()
                        await submission.mod.approve()
                    except Exception as e:
                        logging.error(e)

            # my_tags = []
        except Exception as e:
            logging.error(e)


async def stalker(reddit, config):
    async def watch_submissions(reddit, config, user):
        redditor = await reddit.redditor(user)
        try:
            async for submission in redditor.stream.submissions(skip_existing=True):
                victim = config["reddit"]["stalk"].get(user)

                frequency = victim.get("frequency", 0.1)

                if random.random() > frequency:
                    continue

                await submission.load()
                await submission.subreddit.load()

                op = get_identity(user)

                context = [
                    {
                        "bias": get_identity(),
                        "message": f"/r/{submission.subreddit.display_name}",
                    },
                    {"bias": int(op), "message": submission.title},
                    {"bias": int(op), "message": submission.selftext},
                ]

                stalker = victim.get("stalker", [])

                success, bias, output, seeded = await head.ctx.chat(
                    ctx=context,
                    personas=stalker,
                )

                msg = (
                    submission.title[:66] + "..."
                    if len(submission.title) > 66
                    else submission.title
                )

                print(colors.BLUE + "ONE@REDDIT: " + colors.WHITE + msg)

                if success == False:
                    continue

                if not stalker:
                    daemon = get_daemon(bias)
                    output = transformer(daemon, output)

                asyncio.create_task(
                    reply(
                        submission,
                        output,
                        {
                            "min": victim.get("min", 300),
                            "max": victim.get("max", 900),
                            "seeded": seeded,
                        },
                    )
                )
        except Exception as e:
            logging.error(e)

    async def watch_comments(reddit, config, user):
        redditor = await reddit.redditor(user)
        try:
            async for comment in redditor.stream.comments(skip_existing=True):
                victim = config["reddit"]["stalk"].get(user)

                frequency = victim.get("frequency", 0.1)
                if random.random() > frequency:
                    continue

                await comment.load()
                context = await build_context(comment=comment)

                stalker = victim.get("stalker", [])

                success, bias, output, seeded = await head.ctx.chat(
                    ctx=context,
                    personas=stalker,
                )

                msg = (
                    comment.body[:66] + "..."
                    if len(comment.body) > 66
                    else comment.body
                )
                print(colors.BLUE + "ONE@REDDIT: " + colors.WHITE + msg)

                if success == False:
                    continue

                if not stalker:
                    daemon = get_daemon(bias)
                    output = transformer(daemon, output)

                asyncio.create_task(
                    reply(
                        comment,
                        output,
                        {
                            "min": victim.get("min", 300),
                            "max": victim.get("max", 900),
                            "seeded": seeded,
                        },
                    )
                )
        except Exception as e:
            logging.error(e)

    tasks = {}
    while True:
        if config["reddit"].get("stalk", None) is not None:
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


async def subscribe_submissions(reddit, config):
    try:
        active = []
        subs = config["reddit"]["subs"]
        for sub in subs:
            if subs[sub] is None:
                continue
            if "frequency" in subs[sub]:
                if subs[sub].get("frequency", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        global my_tags
        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "tags" in subs[submission.subreddit.display_name]:
                await submission.load()
                await submission.author.load()
                subreddit = await reddit.subreddit(submission.subreddit.display_name)
                await subreddit.load()
                try:
                    sub_tags = subs[submission.subreddit.display_name].get("tags")
                    tags = sub_tags + my_tags
                    producer(
                        {
                            "event": "new_reddit_submission",
                            "title": submission.title,
                            "description": submission.selftext,
                            "username": "/u/" + submission.author.name,
                            "avatar_url": submission.author.icon_img,
                            "thumbnail": subreddit.community_icon,
                            "link": submission.shortlink,
                            "footer": "/r/" + subreddit.display_name,
                            "tags": set(tags),
                        },
                    )
                    my_tags = []
                except Exception as e:
                    logging.error(e)

            frequency = subs[submission.subreddit.display_name].get("frequency", 0)
            if config["reddit"].get("stalk"):
                if config["reddit"]["stalk"].get(submission.author):
                    frequency = config["reddit"]["stalk"][submission.author].get(
                        "frequency", frequency
                    )

            sub = subs[submission.subreddit.display_name]

            if filter_response(sub, config, submission):
                continue

            if submission.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue
            if random.random() > frequency:
                continue

            op = get_identity()

            persona = sub.get("persona", [])

            context = [
                {
                    "bias": get_identity(),
                    "message": f"/r/{submission.subreddit.display_name}",
                },
                {"bias": int(op), "message": submission.title},
                {"bias": int(op), "message": submission.selftext},
            ]

            success, bias, output, seeded = await head.ctx.chat(
                ctx=context, personas=persona
            )

            msg = (
                submission.title[:66] + "..."
                if len(submission.title) > 66
                else submission.title
            )

            print(colors.BLUE + "ONE@REDDIT: " + colors.WHITE + msg)

            if success == False:
                continue

            if not "persona" in sub:
                daemon = get_daemon(bias)
                output = transformer(daemon, output)

            asyncio.create_task(
                reply(
                    submission,
                    output,
                    {
                        "min": config["reddit"]["delay"].get("min", 300),
                        "max": config["reddit"]["delay"].get("max", 300),
                        "seeded": seeded,
                    },
                )
            )

    except Exception as e:
        logging.error(e)

    asyncio.create_task(subscribe_submissions(reddit, config))


# Subscribe to a single subreddit.
async def subscribe_comments(reddit, config):
    try:
        active = []
        subs = config["reddit"]["subs"]
        for sub in subs:
            if subs[sub] is None:
                continue
            if "frequency" in subs[sub]:
                if subs[sub].get("frequency", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for comment in subreddits.stream.comments(skip_existing=True):
            parent = await comment.parent()
            await parent.load()

            sub_config = config["reddit"]["subs"][comment.subreddit.display_name]

            frequency = sub_config.get("frequency", 0)

            if config["reddit"].get("stalk"):
                stalker_config = config["reddit"]["stalk"].get(
                    str(comment.author), None
                )
                if stalker_config is not None:
                    frequency = stalker_config.get("frequency", frequency)

            roll = random.random()
            if parent.author == os.environ["REDDITAGENT"]:
                frequency = sub_config.get(
                    "followup_frequency",
                    config["reddit"].get("followup_frequency", 0.333),
                )
                if stalker_config is not None:
                    frequency = stalker_config.get("followup_frequency", frequency)

            if roll >= frequency:
                continue

            await comment.load()
            if comment.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue

            context = await build_context(comment=comment)

            persona = sub_config.get("persona", [])

            submission = await reddit.submission(comment.submission)
            if filter_response(sub_config, config, submission, comment):
                continue

            success, bias, output, seeded = await head.ctx.chat(
                ctx=context,
                personas=persona,
            )

            msg = comment.body[:66] + "..." if len(comment.body) > 66 else comment.body
            print(colors.BLUE + "ONE@REDDIT: " + colors.WHITE + msg)

            if success == False:
                continue

            if not "persona" in sub_config:
                daemon = get_daemon(bias)
                output = transformer(daemon, output)

            asyncio.create_task(
                reply(
                    comment,
                    output,
                    {
                        "min": config["reddit"]["delay"].get("min", 300),
                        "max": config["reddit"]["delay"].get("max", 300),
                        "seeded": seeded,
                    },
                )
            )

    except Exception as e:
        logging.error(e)

    asyncio.create_task(subscribe_comments(reddit, config))


def filter_response(sub, config, submission, comment=None):
    if "filter" in sub or "filter" in config["reddit"]:
        filters = config["reddit"].get("filter", []) + sub.get("filter", [])
        for term in filters:
            if term in submission.title.lower() or term in submission.selftext.lower():
                return True
            if comment:
                if term in comment.body.lower():
                    return True
        return False


async def reply(obj, message, config):
    try:
        await asyncio.sleep(
            random.randint(config.get("min", 300), config.get("max", 900))
        )
        await obj.reply(message)

        color = colors.RED
        if config.get("seeded", False) == True:
            color = colors.GREEN

        print(color + "ONE@REDDIT: " + colors.WHITE + message)
    except Exception as e:
        logging.error(e)


# Build context from a chain of comments.
async def build_context(comment):
    context = [{"bias": get_identity(), "message": comment.body}]
    parent = await comment.parent()
    await parent.load()
    while isinstance(parent, asyncpraw.models.Comment):
        await parent.refresh()
        context.insert(0, {"bias": get_identity(), "message": parent.body})
        parent = await parent.parent()
        await parent.load()
    context.insert(
        0, {"bias": get_identity(), "message": f"{parent.title} => {parent.selftext}"}
    )
    return context


# Format the output.
def transformer(name, text):
    pronoun = random.choice(["My", "A"])

    verb = random.choice(["says", "said", "whispers"])
    leader = "Penny"
    minion = "daemon"
    if os.environ["REDDITAGENT"] == "AlexandriaPen":
        leader = "Ink"
        minion = "ghost"
    types = random.choice([minion, "friend", "robot"])
    responses = [
        f'{pronoun} {types} {verb}, "{text}"',
        f'{leader} {verb}, "{text}"',
        f'{name} {verb}, "{text}"',
        f"{text}",
    ]
    return random.choice(responses)
