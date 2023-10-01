import asyncio
import logging
import os
import random
import re
import threading
import traceback
import time
from copy import deepcopy
from pprint import pprint

import asyncpraw
from cerberus import Validator

import head
from common import ad, bc, get_daemon, get_identity, wall, ship
from events import post_event, subscribe_event


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
                    "frequency": {"type": "number"},
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
                    "frequency": {"type": "float"},
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
        try:
            subscribe_event("kb_updated", receive_kb_updates)
            await asyncio.gather(
                subscribe_comments(reddit, config),
                subscribe_submissions(reddit, config),
                stalker(reddit, config),
                manage_submissions(reddit, config),
            )
        except Exception as e:
            logging.error(e)


queued = []


async def receive_kb_updates(title, content, tags):
    queued.append({"title": title, "content": content, "tags": tags})


my_tags = None


async def manage_submissions(reddit, config):
    global my_tags
    global queued
    subreddits = config["reddit"]["subs"]
    while True:
        try:
            await asyncio.sleep(6.66)
            if len(queued) == 0:
                continue
            item = queued.pop(0)
            title = item["title"]
            content = item["content"]
            # This is such a stupid hack, because passing information through
            # multiple events is hard.
            my_tags = item["tags"]
            for name in subreddits:
                sub = subreddits.get(name)
                allowed = False
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
                        break
                if not edited:
                    submission = await subreddit.submit(title=title, selftext=content)
                    try:
                        await submission.load()
                        await submission.mod.approve()
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

                frequency = victim.get("frequency", 0.1)

                if random.random() > frequency:
                    continue

                await submission.load()
                await submission.subreddit.load()

                op = get_identity(user)

                context = [
                    wall
                    + str(get_identity())
                    + ship
                    + " /r/"
                    + submission.subreddit.display_name,
                    wall + str(op) + ship + " " + submission.title,
                    wall + str(op) + ship + " " + submission.selftext,
                ]

                stalker = config["personas"].get(victim.get("stalker", None), None)
                bias = stalker.get("bias", None) if stalker else None
                prefix = (
                    stalker.get("persona")
                    if stalker
                    else "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."
                )

                if bias:
                    prefix = wall + str(bias) + ship + " " + prefix

                success, bias, output, seeded = await head.ctx.chat(
                    ctx=context,
                    bias=bias,
                    prefix=prefix,
                    decay_after_length=66,
                )

                msg = (
                    submission.title[:66] + "..."
                    if len(submission.title) > 66
                    else submission.title
                )
                print(bc.FOLD + "ONE@REDDIT: " + ad.TEXT + msg)

                if success == False:
                    continue

                if not stalker:
                    daemon = get_daemon(bias)
                    output = transformer(daemon, output)

                min_delay = victim.get("min", 300)
                max_delay = victim.get("max", 900)
                asyncio.create_task(
                    reply(
                        submission,
                        output,
                        {"min": min_delay, "max": max_delay, "seeded": seeded},
                    )
                )
            except Exception as e:
                logging.error(e)

    async def watch_comments(reddit, config, user):
        redditor = await reddit.redditor(user)
        async for comment in redditor.stream.comments(skip_existing=True):
            try:
                victim = config["reddit"]["stalk"].get(user)

                frequency = victim.get("frequency", 0.1)
                if random.random() > frequency:
                    continue

                await comment.load()
                context = await build_context(comment=comment)

                stalker = config["personas"].get(victim.get("stalker", None), None)
                bias = stalker.get("bias", None) if stalker else None
                prefix = (
                    stalker.get("prompt")
                    if stalker
                    else "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."
                )

                if bias:
                    prefix = wall + str(bias) + ship + " " + prefix

                success, bias, output, seeded = await head.ctx.chat(
                    ctx=context,
                    bias=bias,
                    prefix=prefix,
                    decay_after_length=66,
                )

                msg = (
                    comment.body[:66] + "..."
                    if len(comment.body) > 66
                    else comment.body
                )
                print(bc.FOLD + "ONE@REDDIT: " + ad.TEXT + msg)

                if success == False:
                    continue

                if not stalker:
                    daemon = get_daemon(bias)
                    output = transformer(daemon, output)

                min_delay = victim.get("min", 300)
                max_delay = victim.get("max", 900)
                asyncio.create_task(
                    reply(
                        comment,
                        output,
                        {"min": min_delay, "max": max_delay, "seeded": seeded},
                    )
                )
            except Exception as e:
                logging.error(e)
                print(traceback.format_exc())

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


async def subscribe_submissions(reddit, config):
    try:
        active = []
        subs = config["reddit"]["subs"]
        for sub in subs:
            if "frequency" in subs[sub]:
                if subs[sub].get("frequency", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "tags" in subs[submission.subreddit.display_name]:
                await submission.load()
                await submission.author.load()
                subreddit = await reddit.subreddit(submission.subreddit.display_name)
                await subreddit.load()
                try:
                    tags = subs[submission.subreddit.display_name].get("tags")
                    global my_tags
                    if my_tags:
                        tags = my_tags + tags
                    post_event(
                        "new_reddit_submission",
                        title=submission.title,
                        description=submission.selftext,
                        username="/u/" + submission.author.name,
                        avatar_url=submission.author.icon_img,
                        thumbnail=subreddit.community_icon,
                        link=submission.shortlink,
                        footer="/r/" + subreddit.display_name,
                        tags=deepcopy(tags),
                    )
                    my_tags = None
                except Exception as e:
                    logging.error(e)

            frequency = subs[submission.subreddit.display_name].get("frequency", 0)

            sub = subs[submission.subreddit.display_name]

            if filter_response(sub, config, submission):
                continue

            if submission.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue
            if random.random() > frequency:
                continue

            op = get_identity()

            bias = None
            prompt = "I carefully respond to a submission on Reddit."

            if "persona" in sub:
                persona = config["personas"].get(sub["persona"])
                bias = persona.get("bias")
                prompt = persona.get("persona")

            context = [
                wall
                + str(get_identity())
                + ship
                + " /r/"
                + submission.subreddit.display_name,
                wall + str(op) + ship + " " + submission.title,
                wall + str(op) + ship + " " + submission.selftext,
            ]
            success, bias, output, seeded = await head.ctx.chat(
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
            print(bc.FOLD + "ONE@REDDIT: " + ad.TEXT + msg)

            if success == False:
                continue
            else:
                daemon = get_daemon(bias)
                if not "persona" in sub:
                    output = transformer(daemon, output)

            min_delay = config["reddit"]["delay"].get("min", 300)
            max_delay = config["reddit"]["delay"].get("max", 300)

            asyncio.create_task(
                reply(
                    submission,
                    output,
                    {"min": min_delay, "max": max_delay, "seeded": seeded},
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
            if "frequency" in config["reddit"]["subs"][sub]:
                if config["reddit"]["subs"][sub].get("frequency", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for comment in subreddits.stream.comments(skip_existing=True):
            parent = await comment.parent()
            await parent.load()

            frequency = config["reddit"]["subs"][comment.subreddit.display_name].get(
                "frequency", 0
            )

            roll = random.random()
            if parent.author == os.environ["REDDITAGENT"]:
                roll = roll / (len("ACTG") * 100)  # the optimal number of children
            if roll >= frequency:
                continue

            await comment.load()
            if comment.author in [os.environ["REDDITAGENT"], "AutoModerator"]:
                continue

            context = await build_context(comment=comment)

            bias = None
            prefix = "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."

            sub = config["reddit"]["subs"][comment.subreddit.display_name]
            if "persona" in sub:
                persona = config["personas"].get(sub["persona"])
                bias = persona.get("bias")
                prefix = wall + str(bias) + ship + " " + persona.get("persona")

            submission = await reddit.submission(comment.submission)
            if filter_response(sub, config, submission, comment):
                continue

            success, bias, output, seeded = await head.ctx.chat(
                ctx=context,
                prefix=prefix,
                decay_after_length=66,
            )

            msg = comment.body[:66] + "..." if len(comment.body) > 66 else comment.body
            print(bc.FOLD + "ONE@REDDIT: " + ad.TEXT + msg)

            if success == False:
                continue

            if not "persona" in sub:
                daemon = get_daemon(bias)
                output = transformer(daemon, output)

            min_delay = config["reddit"]["delay"].get("min", 300)
            max_delay = config["reddit"]["delay"].get("max", 300)

            asyncio.create_task(
                reply(
                    comment,
                    output,
                    {"min": min_delay, "max": max_delay, "seeded": seeded},
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

        color = bc.CORE
        if config.get("seeded", False) == True:
            color = bc.ROOT

        print(color + "ONE@REDDIT: " + ad.TEXT + message)
    except Exception as e:
        logging.error(e)


# Build context from a chain of comments.
async def build_context(comment):
    context = [wall + str(get_identity()) + ship + " " + str(comment.body)]
    parent = await comment.parent()
    await parent.load()
    while isinstance(parent, asyncpraw.models.Comment):
        await parent.refresh()
        context.insert(0, wall + str(get_identity()) + ship + " " + str(parent.body))
        parent = await parent.parent()
        await parent.load()
    context.insert(
        0,
        wall
        + str(get_identity())
        + ship
        + " "
        + str(parent.title)
        + " => "
        + str(parent.selftext),
    )
    return context


# Format the output.
def transformer(name, text):
    pronoun = random.choice(["My", "A"])
    types = random.choice(["daemon", "friend", "robot"])
    verb = random.choice(["says", "said", "wants to say", "whispers", "thinks"])
    responses = [
        f'{pronoun} {types} {verb}, "{text}"',
        f'Penny {verb}, "{text}"',
        f'{name} {verb}, "{text}"',
        f"{text}",
    ]
    return random.choice(responses)
