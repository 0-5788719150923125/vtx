import os
import shutil
import json
import re
import glob
import praw


def spy():
    print("a noun")


def integrate():
    print("sight and sound")


def vision():
    print("a view through my lens")


def ingest():

    isExist = os.path.exists("/lab/texts/discord")
    if isExist:
        shutil.rmtree("/lab/texts/discord")

    os.makedirs("/lab/texts/discord")

    # if os.path.exists("/lab/texts/discord.txt"):
    #     os.remove("/lab/texts/discord.txt")

    print("tried to eat Discord exports")
    for filename in os.listdir("/lab/discord"):
        try:
            with open(os.path.join("/lab/discord", filename), "r") as file:
                try:
                    data = json.load(file)

                    for i in data["messages"]:
                        if i["type"] != "Default" and i["type"] != "Reply":
                            continue
                        if i["content"] == "":
                            continue
                        if i["author"]["isBot"] == True:
                            continue
                        if len(i["mentions"]) > 0:
                            continue

                        txt_file = open("/lab/texts/discord/" + filename + ".txt", "a")

                        try:
                            sanitized = re.sub(r"http\S+", "[REDACTED]", i["content"])
                            content = i["author"]["id"] + ": " + sanitized
                            txt_file.write(f"{content}\n".format(content))
                        except:
                            print("Failed: " + i["id"])
                        txt_file.close()

                    file.close()
                except:
                    print("failed to eat a binary file")
        except:
            print("handling errors")


def read():
    print("scrape reddit")

    isExist = os.path.exists("/lab/texts/reddit")
    if isExist:
        shutil.rmtree("/lab/texts/reddit")

    os.makedirs("/lab/texts/reddit")

    dread = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )
    subreddit = dread.subreddit("stairsofpantheon")

    for sub in subreddit.hot(limit=500):
        try:
            txt = open("/lab/texts/reddit/" + sub.title + ".txt", "a")
            txt.write(sub.title)
            txt.write(sub.selftext)
            txt.close()
        except:
            print("fail reddit")


ingest()
read()
