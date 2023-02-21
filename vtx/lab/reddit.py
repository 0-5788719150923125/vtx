from utils import ad, bc, config, get_identity, propulsion, ship
import asyncpraw
import requests
import random
import head
import json
import os

reddit = asyncpraw.Reddit(
    client_id=os.environ["REDDITCLIENT"],
    client_secret=os.environ["REDDITSECRET"],
    user_agent="u/" + os.environ["REDDITAGENT"],
    username=os.environ["REDDITAGENT"],
    password=os.environ["REDDITPASSWORD"],
)

# Subscribe to a single subreddit
async def subscribe(subreddit):

    try:
        chance = config["reddit"][subreddit].get("chance", 0.01)
        watch = []

        if "watch" not in config["reddit"][subreddit]:
            return
        if config["reddit"][subreddit]["watch"] == True:
            watch.append(subreddit)
        else:
            return

        subreddit = await reddit.subreddit(subreddit, fetch=True)
    except Exception as e:
        print(e)

    async for comment in subreddit.stream.comments(skip_existing=True):
        try:

            roll = random.random()
            if roll >= chance:
                return

            await comment.submission.load()
            parent = await comment.parent()
            submission_title = comment.submission.title
            submission_body = comment.submission.selftext[:222]
            parent_text = None
            if isinstance(parent, asyncpraw.models.Submission):
                parent_text = str(parent.title) + " => " + str(parent.selftext[:222])
            else:
                await parent.load()
                await parent.refresh()
                if parent.author == os.environ["REDDITAGENT"]:
                    continue
                parent_text = str(parent.body)

            await comment.load()
            if comment.author == os.environ["REDDITAGENT"]:
                continue

            p = get_identity()
            c = get_identity()

            ctx = [
                propulsion + str(c) + ship + " " + "You are a chat bot.",
                propulsion + str(p) + ship + " " + "I am a chat bot.",
                propulsion
                + str(c)
                + ship
                + " "
                + submission_title
                + " => "
                + submission_body,
                propulsion + str(p) + ship + " " + parent_text,
                propulsion + str(c) + ship + " " + comment.body,
            ]
            generation = await head.gen(bias=int(get_identity()), ctx=ctx)
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
            obj = {"seed": str(generation[0])}
            response = requests.get("http://ctx:9666/daemon", json=obj)
            daemon = json.loads(response.text)
            response.close()
            output = transformer([daemon["name"], generation[1]])
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
            await comment.reply(output)
        except Exception as e:
            print(e)


# format the output
def transformer(group):
    responses = [
        f'My daemon says, "{group[1]}"',
        f'Penny said, "{group[1]}"',
        f'{group[0]} says, "{group[1]}"',
    ]
    return random.choice(responses)
