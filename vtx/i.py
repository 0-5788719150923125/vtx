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

choices = [
    "[REDACTED]",
    "[CLASSIFIED]",
    "[CORRUPTED]",
]


# https://github.com/Tyrrrz/DiscordChatExporter/wiki/Message-filters
def fetch_from_discord():

    discord_token = os.environ["SELFTOKEN"]

    if not os.path.exists("/lab/dump/discord"):
        os.makedirs("/lab/dump/discord")

    if config["discord"]["all_dms"] == True:
        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "/lab/dump/discord" -f "JSON"'
        os.system(command)

    for server in config["discord"]["servers"]:
        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportguild --guild "{server["id"]}" -t "{discord_token}" -o "/lab/dump/discord" -f "JSON"'
        if "after" in server:
            command.join(" --after " + server["after"])
        os.system(command)


def prep_discord_messages():

    if os.path.exists("/lab/discord"):
        shutil.rmtree("/lab/discord")

    os.makedirs("/lab/discord")

    print("tried to eat Discord exports")
    for filename in os.listdir("/lab/dump/discord"):
        try:
            with open(os.path.join("/lab/dump/discord", filename), "r") as file:
                try:
                    data = json.load(file)

                    for i in data["messages"]:
                        if i["type"] != "Default" and i["type"] != "Reply":
                            continue
                        if i["content"] == "":
                            continue
                        if i["author"]["isBot"] == True:
                            if str(i["author"]["id"]) == "975174695399854150":
                                print("allowing Eliza")
                            elif str(data["guild"]["id"]) == "716611330198732868":
                                print("allowing RSS bot")
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
                                        random.choice(choices),
                                        result["content"],
                                    )
                                    if len(result["mentions"]) > 0:
                                        for mention in result["mentions"]:
                                            sanitized = sanitized.replace(
                                                mention["name"],
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
                            sanitized = re.sub(
                                r"http\S+", random.choice(choices), i["content"]
                            )
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        mention["name"], "<@" + str(mention["id"]) + ">"
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

        if subreddit["skip"] == True:
            print("skipping")
            continue

        name = subreddit["sub"]
        if os.path.exists("/lab/reddit/" + name):
            shutil.rmtree("/lab/reddit/" + name)

        os.makedirs("/lab/reddit/" + name)

        def main():
            for post in reddit.subreddit(name).top(limit=500):
                dump_replies(replies=post.comments, context=[post.title, post.selftext])

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
