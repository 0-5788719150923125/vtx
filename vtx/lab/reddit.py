import random
import os
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import asyncio
import asyncpraw
import head
import requests
from pprint import pprint
from lab.discord import send_webhook

reddit = None


async def orchestrate(config) -> None:
    global reddit
    if reddit:
        await submission(reddit)
        return
    async with asyncpraw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent="u/" + os.environ["REDDITAGENT"],
        username=os.environ["REDDITAGENT"],
        password=os.environ["REDDITPASSWORD"],
    ) as r:
        try:
            reddit = r
            await asyncio.gather(
                subscribe_comments(reddit), subscribe_submissions(reddit)
            )
        except Exception as e:
            print(e)


# Create a submission.
async def submission(reddit):
    try:
        servers = config["reddit"]["TheInk"]["submissions"]
        for server in servers:
            if random.random() > server.get("frequency", 0.00059):
                continue
            print(server)
            subreddit = await reddit.subreddit("TheInk")
            title = server.get("title", "On the 5th of September...")
            webhook = server.get("alert")
            prompt = server.get("prompt", "On the 5th of September, 2024,")
            output = await head.gen(
                prefix=str(prompt),
                max_new_tokens=2048,
                mode="prompt",
                decay_after_length=1024,
                decay_factor=0.00000023,
            )
            if output == False:
                return
            submission = await subreddit.submit(title=title, selftext=output)
            await submission.load()
            await submission.author.load()
            subreddit = await reddit.subreddit(submission.subreddit.display_name)
            await subreddit.load()
            description = str(submission.selftext)[:666] + "..."
            if server.get("simplify", False) == True:
                description = None
            send_webhook(
                webhook_url=webhook,
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
        print(e)


async def subscribe_submissions(reddit):
    try:
        active = []
        for sub in config["reddit"]:
            if "chance" in config["reddit"][sub]:
                if config["reddit"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "alerts" in config["reddit"][submission.subreddit.display_name]:
                webhook = config["reddit"][submission.subreddit.display_name].get(
                    "alerts"
                )
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
                    description=str(submission.selftext)[:666] + "...",
                    thumbnail=subreddit.community_icon,
                    footer="/r/" + subreddit.display_name,
                )

            chance = config["reddit"][submission.subreddit.display_name].get(
                "chance", 0
            )

            if submission.author == os.environ["REDDITAGENT"]:
                continue
            if random.random() > chance:
                continue
            bias = get_identity()
            context = [
                propulsion
                + str(get_identity())
                + ship
                + " /r/"
                + subreddit.display_name,
                propulsion + str(bias) + ship + " " + submission.title,
                propulsion + str(bias) + ship + " " + submission.selftext,
            ]
            generation = await head.gen(
                ctx=context,
                prefix="I carefully respond to a submission on Reddit.",
                decay_after_length=66,
            )
            if not generation:
                continue
            else:
                daemon = get_daemon(generation[0])
                generation = transformer([daemon, generation[1]])
            print(bc.CORE + "ONE@REDDIT: " + ad.TEXT + generation)
            await asyncio.sleep(random.randint(300, 900))
            await submission.reply(generation)

    except Exception as e:
        print(e)


# Subscribe to a single subreddit.
async def subscribe_comments(reddit):
    try:
        active = []
        for sub in config["reddit"]:
            if "chance" in config["reddit"][sub]:
                if config["reddit"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for comment in subreddits.stream.comments(skip_existing=True):
            await comment.submission.load()
            parent = await comment.parent()
            await parent.load()

            chance = config["reddit"][comment.subreddit.display_name].get("chance", 0)

            roll = random.random()
            if parent.author == os.environ["REDDITAGENT"]:
                roll = roll / (len("ACTG") * 100)  # the optimal number of children
            if roll >= chance:
                continue

            await comment.load()
            if comment.author == os.environ["REDDITAGENT"]:
                continue

            context = await build_context(comment=comment)

            generation = await head.gen(
                ctx=context,
                prefix="I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit.",
                decay_after_length=66,
            )

            if generation[0] == "error":
                continue

            daemon = get_daemon(generation[0])
            output = transformer([daemon, generation[1]])
            await asyncio.sleep(random.randint(300, 900))
            await comment.reply(output)

            color = bc.CORE
            if generation[2] == True:
                color = bc.ROOT

            print(color + "INK@REDDIT: " + ad.TEXT + output)

    except Exception as e:
        print(e)


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
