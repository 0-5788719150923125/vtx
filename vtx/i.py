import os
import shutil
import json
import re
import glob
import praw
import time
import yaml
import random
import numpy as np
import secrets
import requests
from bs4 import BeautifulSoup
from mergedeep import merge, Strategy
import pprint

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    print("trying to load user config")
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    print("using default config")
    config = default_config

propulsion = "¶"
ship = ":>"


def crawl(site="https://ink.university"):
    html = requests.get(site).content
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    internal_links = []
    for link in links:
        href = link.get("href")
        if href.startswith("/"):
            internal_links.append(site + href)
    print(internal_links)
    return internal_links


def fetch_from_discord():

    discord_token = os.environ["DISCORDTOKEN"]
    if "use_self_token" in config["discord"]:
        if config["discord"]["use_self_token"] == True:
            discord_token = os.environ["SELFTOKEN"]

    if not os.path.exists("/lab/raw/discord"):
        os.makedirs("/lab/raw/discord")

    if config["discord"]["export_dms"] == True:
        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "/lab/raw/discord" -f "JSON"'
        os.system(command)

    for server in config["discord"]["servers"]:
        skip = False
        if "skip" in server:
            skip = server["skip"]
            if skip == True:
                continue

        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportguild --guild "{server}" -t "{discord_token}" -o "/lab/raw/discord" -f "JSON"'
        if "before" in server:
            command.join(" --before " + server["before"])
        if "after" in server:
            command.join(" --after " + server["after"])
        os.system(command)


def prepare_discord_messages():

    urls = crawl("https://ink.university")

    if os.path.exists("/lab/discord"):
        shutil.rmtree("/lab/discord")

    os.makedirs("/lab/discord")

    print("preparing Discord messages")
    for filename in os.listdir("/lab/raw/discord"):
        try:
            with open(os.path.join("/lab/raw/discord", filename), "r") as file:
                data = json.load(file)

                for i in data["messages"]:

                    if i["type"] != "Default" and i["type"] != "Reply":
                        continue
                    if i["content"] == "":
                        continue
                    if i["author"]["isBot"] == True:
                        if str(i["author"]["id"]) == "975174695399854150":  # Eliza
                            pass
                        elif str(i["author"]["id"]) == "1055993037077106718":  # Samn
                            pass
                        else:
                            continue

                    with open("/lab/discord/" + filename + ".txt", "a") as txt_file:

                        if i["type"] == "Reply":
                            try:
                                message_ref_id = i["reference"]["messageId"]
                                result = next(
                                    (
                                        obj
                                        for obj in data["messages"]
                                        if obj["id"] == message_ref_id
                                    ),
                                    None,
                                )
                                if result is not None:
                                    sanitized = re.sub(
                                        r"http\S+",
                                        secrets.choice(urls),
                                        result["content"],
                                    )
                                    if len(result["mentions"]) > 0:
                                        for mention in result["mentions"]:
                                            sanitized = sanitized.replace(
                                                "@" + mention["name"],
                                                "<@" + str(mention["id"]) + ">",
                                            )
                                    content = (
                                        propulsion
                                        + result["author"]["id"]
                                        + ship
                                        + " "
                                        + sanitized
                                    )
                                    txt_file.write(f"{content}\n".format(content))
                            except Exception as e:
                                print(e)
                                print("failed to prepare a reply")

                        try:
                            sanitized = re.sub(
                                r"http\S+", secrets.choice(urls), i["content"]
                            )
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        "@" + mention["name"],
                                        "<@" + str(mention["id"]) + ">",
                                    )

                            content = (
                                propulsion + i["author"]["id"] + ship + " " + sanitized
                            )
                            txt_file.write(f"{content}\n".format(content))
                        except:
                            print("Failed: " + i["id"])

        except:
            print("found a bad file")


def fetch_from_reddit():

    urls = crawl("https://pen.university")

    reddit = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )

    for sub in config["reddit"]:

        name = sub

        skip = False
        if "skip" in config["reddit"][sub]:
            skip = config["reddit"][sub]["skip"]

        limit = 50
        if "limit" in config["reddit"][sub]:
            limit = config["reddit"][sub]["limit"]

        if skip == True:
            continue
        else:
            print("archiving " + name)

        if os.path.exists("/lab/reddit/" + name):
            shutil.rmtree("/lab/reddit/" + name)

        os.makedirs("/lab/reddit/" + name)

        identities = {}

        def main():
            for submission in reddit.subreddit(name).top(limit=limit):

                bias = get_identity()
                print("wrote to " + str(bias))

                context = []
                with open(
                    "/lab/reddit/" + name + "/" + submission.id + ".txt", "a"
                ) as file:
                    sanitized = re.sub(
                        r"http\S+",
                        secrets.choice(urls),
                        propulsion
                        + str(bias)
                        + ship
                        + " "
                        + submission.title
                        + " "
                        + submission.selftext.replace("\n", "\\n"),
                    )
                    context = [sanitized]
                    file.write("".join(context))
                dump_replies(
                    replies=submission.comments,
                    context=context,
                )

        def dump_replies(replies, context):

            for reply in replies:
                if isinstance(reply, praw.models.MoreComments):
                    continue

                bias = get_identity()
                print("wrote to " + str(bias))

                with open(
                    "/lab/reddit/" + name + "/" + reply.submission.id + ".txt", "a"
                ) as file:
                    sanitized = re.sub(
                        r"http\S+",
                        secrets.choice(urls),
                        propulsion
                        + str(bias)
                        + ship
                        + " "
                        + reply.body.replace("\n", "\\n"),
                    )
                    context.append(sanitized)
                    file.write("\n" + " ".join(context))

                dump_replies(reply.replies, context)
                context.pop()

        main()


def get_identity():
    count = secrets.choice([18, 19])
    identity = "".join(secrets.choice("0123456789") for i in range(count))
    return identity


class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"
    ENDC = "\033[0m"
