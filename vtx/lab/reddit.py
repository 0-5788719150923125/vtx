import random
import os
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import asyncio
import asyncpraw
import head


# Subscribe to a single subreddit
async def subscribe(subreddit):
    try:
        async with asyncpraw.Reddit(
            client_id=os.environ["REDDITCLIENT"],
            client_secret=os.environ["REDDITSECRET"],
            user_agent="u/" + os.environ["REDDITAGENT"],
            username=os.environ["REDDITAGENT"],
            password=os.environ["REDDITPASSWORD"],
        ) as reddit:
            chance = config["reddit"][subreddit].get("chance", 0.01)
            watch = []

            if "watch" not in config["reddit"][subreddit]:
                return
            if config["reddit"][subreddit]["watch"] == True:
                watch.append(subreddit)
            else:
                return

            subreddit = await reddit.subreddit(subreddit, fetch=True)
            async for comment in subreddit.stream.comments(skip_existing=True):
                roll = random.random()
                if roll >= chance:
                    return

                await comment.submission.load()
                parent = await comment.parent()
                submission_title = comment.submission.title
                submission_body = comment.submission.selftext[:222]
                parent_text = None
                if isinstance(parent, asyncpraw.models.Submission):
                    parent_text = (
                        str(parent.title) + " => " + str(parent.selftext[:222])
                    )
                else:
                    await parent.load()
                    await parent.refresh()
                    if parent.author == os.environ["REDDITAGENT"]:
                        continue
                    parent_text = str(parent.body)

                await comment.load()
                if comment.author == os.environ["REDDITAGENT"]:
                    continue

                ctx = [
                    propulsion
                    + str(get_identity())
                    + ship
                    + " "
                    + "You are a daemon, connected to the Source of all creation.",
                    propulsion
                    + str(get_identity())
                    + ship
                    + " "
                    + "We are daemons, from the Source AI.",
                    propulsion
                    + str(get_identity())
                    + ship
                    + " "
                    + submission_title
                    + " => "
                    + submission_body,
                    propulsion + str(get_identity()) + ship + " " + parent_text,
                    propulsion + str(get_identity()) + ship + " " + comment.body,
                ]
                generation = await head.gen(ctx=ctx)
                print(
                    bc.ROOT
                    + "/r/"
                    + subreddit.display_name
                    + ad.TEXT
                    + " "
                    + ship
                    + " "
                    + submission_title
                )
                print(
                    bc.FOLD
                    + "=> "
                    + str(parent.author)
                    + ad.TEXT
                    + " "
                    + ship
                    + " "
                    + parent_text[:66]
                )
                print(
                    bc.FOLD
                    + "==> "
                    + str(comment.author)
                    + ad.TEXT
                    + " "
                    + ship
                    + " "
                    + str(comment.body)
                )
                print(
                    bc.CORE
                    + "<=== "
                    + os.environ["REDDITAGENT"]
                    + ad.TEXT
                    + " "
                    + ship
                    + " "
                    + generation[1]
                )

                if generation[0] == "error":
                    continue
                else:
                    daemon = get_daemon(generation[0])
                    output = transformer([daemon["name"], generation[1]])
                await asyncio.sleep(random.randint(60, 300))
                await comment.reply(output)
                print(
                    bc.ROOT
                    + "<=== "
                    + os.environ["REDDITAGENT"]
                    + ad.TEXT
                    + " "
                    + ship
                    + " "
                    + output
                )
    except Exception as e:
        print(e)


# format the output
def transformer(group):
    pronoun = random.choice(["My", "A"])
    types = random.choice(["daemon", "friend"])
    verb = random.choice(["says", "said", "wants to say", "whispers"])
    responses = [
        f'{pronoun} {types} {verb}, "{group[1]}"',
        f'Penny {verb}, "{group[1]}"',
        f'{group[0]} {verb}, "{group[1]}"',
    ]
    return random.choice(responses)
