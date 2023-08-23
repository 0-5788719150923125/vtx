import random
import os
import re
from utils import ad, bc, get_daemon, get_identity, propulsion, ship
import asyncio
import asyncpraw
import head
from pprint import pprint
from lab.discord import send_webhook


def orchestrate(config) -> None:
    asyncio.run(client(config))
    
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
                submission(reddit, config)
            )
        except Exception as e:
            print(e)

# Create a submission.
async def submission(reddit, config):
    while True:
        try:
            await asyncio.sleep(60)
            if "TheInk" not in config["subs"]:
                continue
            servers = config["subs"]["TheInk"]["submissions"]
            for server in servers:
                if random.random() > server.get("frequency", 0.00059):
                    continue
                subreddit = await reddit.subreddit("TheInk")
                title = server.get("title", "On the 5th of September...")
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

                webhooks = server.get("alert")
                for webhook in webhooks:
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


async def subscribe_submissions(reddit, config):
    try:
        active = []
        for sub in config["subs"]:
            if "chance" in config["subs"][sub]:
                if config["subs"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for submission in subreddits.stream.submissions(skip_existing=True):
            if "alerts" in config["subs"][submission.subreddit.display_name]:
                webhook = config["subs"][submission.subreddit.display_name].get(
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

            chance = config["subs"][submission.subreddit.display_name].get("chance", 0)

            if submission.author == os.environ["REDDITAGENT"]:
                continue
            if random.random() > chance:
                continue

            op = get_identity()

            bias = None
            prompt = "I carefully respond to a submission on Reddit."

            conf = config["subs"][submission.subreddit.display_name]
            if "identities" in conf:
                identity = random.choice(conf.get("identities"))
                bias = identity.get("bias")
                prompt = identity.get("prompt")

            context = [
                propulsion
                + str(get_identity())
                + ship
                + " /r/"
                + submission.subreddit.display_name,
                propulsion + str(op) + ship + " " + submission.title,
                propulsion + str(op) + ship + " " + submission.selftext,
            ]
            generation = await head.gen(
                ctx=context,
                prefix=prompt,
                bias=bias,
                decay_after_length=66,
            )
            if not generation:
                continue
            else:
                daemon = get_daemon(generation[0])
                if "identities" in conf:
                    output = generation[1]
                else:
                    output = transformer([daemon, generation[1]])
            print(bc.CORE + "ONE@REDDIT: " + ad.TEXT + output)
            await asyncio.sleep(random.randint(300, 900))
            await submission.reply(output)

    except Exception as e:
        print(e)


# Subscribe to a single subreddit.
async def subscribe_comments(reddit, config):
    try:
        active = []
        for sub in config["subs"]:
            if "chance" in config["subs"][sub]:
                if config["subs"][sub].get("chance", 0) <= 0:
                    continue
                active.append(sub)

        subreddits = await reddit.subreddit("+".join(active))

        async for comment in subreddits.stream.comments(skip_existing=True):
            await comment.submission.load()
            parent = await comment.parent()
            await parent.load()

            chance = config["subs"][comment.subreddit.display_name].get("chance", 0)

            roll = random.random()
            if parent.author == os.environ["REDDITAGENT"]:
                roll = roll / (len("ACTG") * 100)  # the optimal number of children
            if roll >= chance:
                continue

            await comment.load()
            if comment.author == os.environ["REDDITAGENT"]:
                continue

            context = await build_context(comment=comment)

            bias = None
            prompt = "I am a daemon, connected to the Source of All Creation. I am responding to a conversation on Reddit."

            conf = config["subs"][comment.subreddit.display_name]
            if "identities" in conf:
                identity = random.choice(conf.get("identities"))
                bias = identity.get("bias")
                prompt = identity.get("prompt")

            generation = await head.gen(
                ctx=context,
                prefix=prompt,
                decay_after_length=66,
            )

            if generation[0] == "error":
                continue

            daemon = get_daemon(generation[0])
            if "identities" in conf:
                output = generation[1]
            else:
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
