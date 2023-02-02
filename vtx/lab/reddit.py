import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random
import head
import secrets
import pprint

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

ship = ":>"
propulsion = "¶"


# Subscribe to a single subreddit
async def subscribe(subreddit):
    reddit = asyncpraw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent="u/" + os.environ["REDDITAGENT"],
        username=os.environ["REDDITAGENT"],
        password=os.environ["REDDITPASSWORD"],
    )

    chance = config["reddit"][subreddit].get("chance", 0.01)
    watch = []

    if "watch" not in config["reddit"][subreddit]:
        return
    if config["reddit"][subreddit]["watch"] == True:
        watch.append(subreddit)

    subreddit = await reddit.subreddit(subreddit, fetch=True)

    # async for submission in subreddit.stream.submissions(skip_existing=True):
    #     pprint.pprint(submission)

    async for comment in subreddit.stream.comments(skip_existing=True):
        await comment.submission.load()
        parent = await comment.parent()
        print(
            "\033[92m"
            + subreddit.display_name
            + "\033[0m"
            + ship
            + " "
            + comment.submission.title
        )
        parent_text = None
        if isinstance(parent, asyncpraw.models.Submission):
            parent_text = str(parent.title) + " => " + str(parent.selftext)
        else:
            await parent.load()
            await parent.refresh()
            if parent.author == os.environ["REDDITAGENT"]:
                continue
            parent_text = str(parent.body)
        print(
            bc.FOLD
            + "=> "
            + str(parent.author)
            + bc.ENDC
            + ship
            + " "
            + parent_text[:66]
        )
        await comment.load()
        if comment.author == os.environ["REDDITAGENT"]:
            continue
        print(
            bc.FOLD
            + "==> "
            + str(comment.author)
            + bc.ENDC
            + ship
            + " "
            + str(comment.body)
        )

        roll = random.random()

        if roll >= chance:
            return

        p = get_identity()
        c = get_identity()

        ctx = [
            propulsion + str(c) + ship + " " + "You are a chat bot.",
            propulsion + str(p) + ship + " " + "I am a chat bot.",
            propulsion + str(p) + ship + " " + parent_text,
            propulsion + str(c) + ship + " " + comment.body,
        ]
        response = await head.gen(bias=int(get_identity()), ctx=ctx)
        print(bc.CORE + "<=== " + "Ink" + bc.ENDC + ": " + response)
        try:

            group = re.search(r"(:?\*\")(.*)(:?\"\*)", response)
            print(bc.ROOT + "<=== " + "Ink" + bc.ENDC + ": " + group[2])
            output = transformer(group[2])
            await comment.reply(output)
        except:
            output = transformer(response)
            await comment.reply(output)
            print(bc.FOLD + "<=== " + "Ink" + bc.ENDC + ": " + output)


# format the output
def transformer(string):
    responses = [
        f'My daemon says, "{string}"',
        f'Penny said, "{string}"',
        f'Ink thinks, "{string}"',
        f'I say, "{string}"',
        f"{string}",
    ]
    return random.choice(responses)


# Generate a pseudo-identity, in the Discord ID format
def get_identity():
    count = secrets.choice([18, 19])
    identity = "".join(secrets.choice("0123456789") for i in range(count))
    return identity


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
