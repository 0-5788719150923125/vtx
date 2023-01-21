import os
import shutil
import json
import re
import glob
import praw
import time
import jsonlines
import yaml
import random
import numpy as np
import secrets

with open("config.yml", "r") as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)


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

        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportguild --guild "{server["id"]}" -t "{discord_token}" -o "/lab/raw/discord" -f "JSON"'
        if "before" in server:
            command.join(" --before " + server["before"])
        if "after" in server:
            command.join(" --after " + server["after"])
        os.system(command)


def prepare_discord_messages():

    if os.path.exists("/lab/discord"):
        shutil.rmtree("/lab/discord")

    os.makedirs("/lab/discord")

    print("preparing Discord messages")
    for filename in os.listdir("/lab/raw/discord"):
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
                                    "",
                                    result["content"],
                                )
                                if len(result["mentions"]) > 0:
                                    for mention in result["mentions"]:
                                        sanitized = sanitized.replace(
                                            "@" + mention["name"],
                                            "<@" + str(mention["id"]) + ">",
                                        )
                                content = (
                                    ":>" + result["author"]["id"] + ": " + sanitized
                                )
                                txt_file.write(f"{content}\n".format(content))
                        except Exception as e:
                            print(e)
                            print("failed to prepare a reply")

                    try:
                        sanitized = re.sub(r"http\S+", "", i["content"])
                        if len(i["mentions"]) > 0:
                            for mention in i["mentions"]:
                                sanitized = sanitized.replace(
                                    "@" + mention["name"],
                                    "<@" + str(mention["id"]) + ">",
                                )

                        content = ":>" + i["author"]["id"] + ": " + sanitized
                        txt_file.write(f"{content}\n".format(content))
                    except:
                        print("Failed: " + i["id"])


def fetch_from_reddit():

    reddit = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )

    for subreddit in config["reddit"]:

        name = subreddit["sub"]

        skip = False
        if "skip" in subreddit:
            skip = subreddit["skip"]

        if skip == True:
            continue
        else:
            print("archiving " + name)

        if os.path.exists("/lab/reddit/" + name):
            shutil.rmtree("/lab/reddit/" + name)

        os.makedirs("/lab/reddit/" + name)

        identities = {}

        def main():
            for submission in reddit.subreddit(name).top(limit=500):

                bias = get_identity()
                print("wrote to " + str(bias))

                context = []
                with open(
                    "/lab/reddit/" + name + "/" + submission.id + ".txt", "a"
                ) as file:
                    context = [
                        ":>"
                        + str(bias)
                        + ": "
                        + submission.title
                        + " "
                        + submission.selftext.replace("\n", "\\n")
                    ]
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
                    context.append(
                        ":>" + str(bias) + ": " + reply.body.replace("\n", "\\n")
                    )
                    file.write("\n" + " ".join(context))

                dump_replies(reply.replies, context)
                context.pop()

        main()


def get_identity():
    identity = "".join(secrets.choice("0123456789") for i in range(18))
    return identity


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
