import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random

with open("/vtx/defaults.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        pprint.pprint(config)
except:
    config = default_config


async def subscribe(subreddit):
    reddit = asyncpraw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent="u/" + os.environ["REDDITAGENT"],
        username=os.environ["REDDITAGENT"],
        password=os.environ["REDDITPASSWORD"],
    )

    watch = []

    for sub in config["reddit"]:
        if "watch" not in config["reddit"][sub]:
            continue
        if config["reddit"][sub]["watch"] == True:
            watch.append(sub)

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
                print(bcolors.FOLD + "=> " + bcolors.ENDC + str(parent.author))
                + ": "
                + str(parent.title)
                + " | "
                + str(parent.selftext)
            )
        else:
            await parent.load()
            await parent.refresh()
            print(
                bcolors.FOLD
                + "=> "
                + str(parent.author)
                + ": "
                + bcolors.ENDC
                + str(parent.body)
            )
        await comment.load()
        print(
            bcolors.FOLD
            + "==> "
            + str(comment.author)
            + ": "
            + bcolors.ENDC
            + str(comment.body)
        )
        chance = 1
        count = random.randint(0, 2)
        if comment.subreddit.display_name in config["reddit"]:
            if config["reddit"][comment.subreddit.display_name]["chance"]:
                chance = config["reddit"][comment.subreddit.display_name]["chance"]
        if count <= chance:
            print(
                bcolors.CORE + "<=== " + "Samn: " + bcolors.FAIL + "test" + bcolors.ENDC
            )
            # comment.reply("test!!")


class bcolors:
    HEADER = "\033[95m"
    FOLD = "\033[94m"
    OKCYAN = "\033[96m"
    ROOT = "\033[92m"
    WARNING = "\033[93m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
