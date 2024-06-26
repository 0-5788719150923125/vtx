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
from common import colors, get_daemon, get_identity, predict_images
from events import consumer, producer
from memory import KeyValue


def main(config) -> None:
    result = validation(config["reddit"])
    if not result:
        return
    asyncio.run(client(config))


if __name__ == "__main__":
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
                    "vote": {
                        "type": "dict",
                        "schema": {
                            "up": {"type": "float"},
                            "down": {"type": "float"},
                            "min": {"type": "integer"},
                            "max": {"type": "integer"},
                        },
                    },
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


async def manage_submissions(reddit, config):
    db = KeyValue("reddit")
    subreddits = config["reddit"]["subs"]

    while True:
        try:
            await asyncio.sleep(6.66)
            item = consumer("book_updated")
            if not item:
                continue

            title = item["title"]
            content = item["content"]

            for name in subreddits:
                sub = subreddits.get(name, {})
                if "tags" not in sub:
                    continue

                target = sub["tags"][0]
                if target not in item["tags"]:
                    continue

                # We submit to the first tag found
                subreddit = await reddit.subreddit(name)

                result = db.query("title", title)

                if result:
                    submission = await fetch_submission_by_id(reddit, result[0]["id"])
                    await submission.edit(body=content)
                    await submission.mod.approve()
                else:
                    submission = await subreddit.submit(title=title, selftext=content)
                    await submission.load()
                    await submission.mod.approve()
                    db.insert({"id": submission.id, "title": title})

                break

        except Exception as e:
            traceback.format_exc()


async def fetch_submission_by_id(reddit, submission_id):
    submission = await reddit.submission(id=submission_id)
    await submission.load()
    return submission


async def get_vote(user):
    up = random.random()
    down = random.random()
    use_up = lambda up, down: up > down
    vote = user.get("vote", {})
    await asyncio.sleep(random.randint(vote.get("min", 60), vote.get("max", 900)))
    if up > down:
        if up < vote.get("up", 0):
            return True
    if down > up:
        if down < vote.get("down", 0):
            return False


async def cast_vote(user, content):
    vote = await get_vote(user)
    if vote in [True, False]:
        await content.load()
        if vote:
            await content.upvote()
            print(
                colors.RED
                + "ONE@REDDIT: "
                + colors.WHITE
                + f"(upvoting content from /u/{content.author})"
            )
        else:
            await content.downvote()
            print(
                colors.RED
                + "ONE@REDDIT: "
                + colors.WHITE
                + f"(downvoting content from /u/{content.author})"
            )


async def stalker(reddit, config):
    async def watch_submissions(reddit, config, user):
        redditor = await reddit.redditor(user)
        try:
            async for submission in redditor.stream.submissions(skip_existing=True):
                victim = config["reddit"]["stalk"].get(user)

                asyncio.create_task(cast_vote(victim, submission))

                frequency = victim.get("frequency", 0)

                if random.random() > frequency:
                    continue

                await submission.load()
                await submission.subreddit.load()

                op = get_identity(user)

                context = [
                    {
                        "bias": int(op),
                        "message": f"{submission.title} (/r/{submission.subreddit.display_name})",
                    },
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

                asyncio.create_task(cast_vote(victim, comment))

                frequency = victim.get("frequency", 0)
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

                if success == False:
                    continue

                print(colors.BLUE + "ONE@REDDIT: " + colors.WHITE + msg)

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

        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "tags" in subs[submission.subreddit.display_name]:
                await submission.load()
                await submission.author.load()
                subreddit = await reddit.subreddit(submission.subreddit.display_name)
                await subreddit.load()
                tags = subs[submission.subreddit.display_name].get("tags")
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
                    "bias": int(op),
                    "message": f"{submission.title} (/r/{submission.subreddit.display_name})",
                },
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

            msg = comment.body[:66] + "..." if len(comment.body) > 66 else comment.body
            print(
                colors.BLUE
                + "ONE@REDDIT:"
                + colors.WHITE
                + f" (/r/{comment.subreddit.display_name}) "
                + msg
            )

            success, bias, output, seeded = await head.ctx.chat(
                ctx=context,
                personas=persona,
            )

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
    target_message = comment.body

    images = await predict_images(target_message)
    if len(images) > 0:
        pred = f"(contains images: {', '.join(images)})"
        print(colors.GREEN + "ONE@REDDIT: " + colors.WHITE + pred)
        target_message += f"\n{pred}"

    context = [{"bias": get_identity(), "message": target_message}]
    parent = await comment.parent()
    await parent.load()
    while isinstance(parent, asyncpraw.models.Comment):
        await parent.refresh()
        context.insert(0, {"bias": get_identity(), "message": parent.body})
        parent = await parent.parent()
        await parent.load()
    context.insert(
        0, {"bias": get_identity(), "message": f"{parent.title}\n\n{parent.selftext}"}
    )
    return context


# Format the output.
def transformer(name, text):
    pronoun = random.choice(["My", "A"])

    verb = random.choice(["says", "said", "whispers"])
    leader = "Penny"
    minion = "daemon"

    types = random.choice([minion, "friend", "robot"])
    responses = [
        f'{pronoun} {types} {verb}, "{text}"',
        f'{leader} {verb}, "{text}"',
        f'{name} {verb}, "{text}"',
        f'People say, "{text}"',
        f"{text}",
        f"{text}",
        f"{text}",
    ]
    return random.choice(responses)
