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
            subscribe_event("kb_updated", load_submissions)
            await asyncio.gather(
                subscribe_comments(reddit, config),
                subscribe_submissions(reddit, config),
                stalker(reddit, config),
                manage_submissions(reddit, config),
            )
        except Exception as e:
            logging.error(e)


queued = []


async def load_submissions(title, content, tags):
    queued.append({"title": title, "content": content, "tags": tags})


async def manage_submissions(reddit, config):
    global queued
    subreddit = await reddit.subreddit("TheInk")
    edited = False
    try:
        while True:
            await asyncio.sleep(6.66)
            if len(queued) > 0:
                item = queued.pop(0)
                title = item["title"]
                content = item["content"]
                tags = item["tags"]
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
                    await submission.load()
                    await submission.mod.approve()
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

                frequency = victim.get("frequency", 0.1)
                if random.random() > frequency:
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
                    post_event(
                        "new_reddit_submission",
                        title=submission.title,
                        description=submission.selftext,
                        username="/u/" + submission.author.name,
                        avatar_url=submission.author.icon_img,
                        thumbnail=subreddit.community_icon,
                        link=submission.shortlink,
                        footer="/r/" + subreddit.display_name,
                        tags=subs[submission.subreddit.display_name].get("tags"),
                    )
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
            prompt = "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."

            sub = config["reddit"]["subs"][comment.subreddit.display_name]
            if "persona" in sub:
                persona = config["personas"].get(sub["persona"])
                bias = persona.get("bias")
                prompt = persona.get("persona")

            submission = await reddit.submission(comment.submission)
            if filter_response(sub, config, submission, comment):
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
