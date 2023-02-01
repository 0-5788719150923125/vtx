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

    chance = config["reddit"][subreddit].get("chance", 33)
    watch = []

    if "watch" not in config["reddit"][subreddit]:
        return
    if config["reddit"][subreddit]["watch"] == True:
        watch.append(subreddit)

    subreddit = await reddit.subreddit(subreddit, fetch=True)
    async for comment in subreddit.stream.comments(skip_existing=True):
        await comment.submission.load()
        parent = await comment.parent()
        print(
            subreddit.display_name
            + ": "
            + "\033[92m"
            + comment.submission.title
            + "\033[0m"
        )
        if isinstance(parent, asyncpraw.models.Submission):
            (
                print(bc.FOLD + "=> " + bc.ENDC + str(parent.author))
                + ": "
                + str(parent.title)
                + " | "
                + str(parent.selftext)
            )
        else:
            await parent.load()
            await parent.refresh()
            print(
                bc.FOLD + "=> " + str(parent.author) + ": " + bc.ENDC + str(parent.body)
            )
        await comment.load()
        print(
            bc.FOLD + "==> " + str(comment.author) + ": " + bc.ENDC + str(comment.body)
        )

        roll = random.randint(0, 100)

        if roll >= chance:
            return

        p = get_identity()
        c = get_identity()

        ctx = [
            propulsion + str(c) + ship + " " + "You are a chat bot.",
            propulsion + str(p) + ship + " " + "I am a chat bot.",
            propulsion + str(p) + ship + " " + parent.body,
            propulsion + str(c) + ship + " " + comment.body,
        ]
        print(bc.CORE + "<=== " + "LuciferianInk: " + bc.ENDC + "generating a response")
        response = await head.gen(bias=int(get_identity()), ctx=ctx)
        print(bc.CORE + "<=== " + "LuciferianInk: " + bc.ENDC + response)
        try:

            group = re.search(r"(:?\*\")(.*)(:?\"\*)", response)
            print(bc.ROOT + "<=== " + "LuciferianInk: " + bc.ENDC + group[2])
            output = transformer(group[2])
            await comment.reply(output)
        except:
            output = transformer(response)
            await comment.reply(output)
            print(bc.FOLD + "<=== " + "LuciferianInk: " + bc.ENDC + output)


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
