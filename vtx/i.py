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
        try:
            with open(os.path.join("/lab/raw/discord", filename), "r") as file:
                try:
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

                        txt_file = open("/lab/discord/" + filename + ".txt", "a")

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
                        txt_file.close()

                    file.close()
                except:
                    print("failed to eat a binary file")
        except:
            print("handling errors")


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

        def main():
            for post in reddit.subreddit(name).top(limit=500):
                dump_submission(post)
                dump_replies(replies=post.comments, context=[post.title, post.selftext])

        def dump_submission(submission):
            with jsonlines.open(
                "/lab/reddit/" + name + "/" + submission.id + ".jsonl",
                mode="a",
            ) as writer:
                writer.write(
                    {
                        "id": submission.id,
                        "context": [submission.title, submission.selftext],
                    }
                )

        def dump_replies(replies, context):

            for reply in replies:
                if isinstance(reply, praw.models.MoreComments):
                    continue

                reply_data = {
                    "id": reply.id,
                    "context": context,
                    "response": reply.body,
                }
                with jsonlines.open(
                    "/lab/reddit/" + name + "/" + reply.submission.id + ".jsonl",
                    mode="a",
                ) as writer:
                    writer.write(reply_data)

                context.append(reply.body)
                dump_replies(reply.replies, context)
                context.pop()

        main()
