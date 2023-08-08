import random
import os
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import asyncio
import asyncpraw
import head


# Create a submission.
async def submission(prompt: str = "On the 5th of September,"):
    try:
        async with asyncpraw.Reddit(
            client_id=os.environ["REDDITCLIENT"],
            client_secret=os.environ["REDDITSECRET"],
            user_agent="u/" + os.environ["REDDITAGENT"],
            username=os.environ["REDDITAGENT"],
            password=os.environ["REDDITPASSWORD"],
        ) as reddit:
            subreddit = await reddit.subreddit("TheInk")
            title = "On the 5th of September..."
            output = await head.gen(
                prefix=str(prompt),
                max_new_tokens=1536,
                mode="prompt",
                decay_after_length=512,
                decay_factor=0.00000023,
            )
            if output == False:
                return
            await subreddit.submit(title=title, selftext=output)

    except Exception as e:
        pass
        # print(e)


async def subscribe_submissions(subreddit):
    try:
        chance = config["reddit"][subreddit].get("chance", 0.0)

        if chance <= 0.0:
            return

        async with asyncpraw.Reddit(
            client_id=os.environ["REDDITCLIENT"],
            client_secret=os.environ["REDDITSECRET"],
            user_agent="u/" + os.environ["REDDITAGENT"],
            username=os.environ["REDDITAGENT"],
            password=os.environ["REDDITPASSWORD"],
        ) as reddit:
            subreddit = await reddit.subreddit(subreddit, fetch=True)
            async for submission in subreddit.stream.submissions(skip_existing=True):
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
        pass
        # print(e)


# Subscribe to a single subreddit.
async def subscribe_comments(subreddit):
    try:
        chance = config["reddit"][subreddit].get("chance", 0)

        if chance <= 0.0:
            return

        async with asyncpraw.Reddit(
            client_id=os.environ["REDDITCLIENT"],
            client_secret=os.environ["REDDITSECRET"],
            user_agent="u/" + os.environ["REDDITAGENT"],
            username=os.environ["REDDITAGENT"],
            password=os.environ["REDDITPASSWORD"],
        ) as reddit:
            subreddit = await reddit.subreddit(subreddit, fetch=True)
            async for comment in subreddit.stream.comments(skip_existing=True):
                await comment.submission.load()
                parent = await comment.parent()
                await parent.load()

                roll = random.random()
                if parent.author == os.environ["REDDITAGENT"]:
                    roll = roll / (len("ACTG") * 100)  # the optimal number of children
                if roll >= chance:
                    return

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
        pass
        # print("subreddit at " + str(subreddit))
        # print(e)


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
