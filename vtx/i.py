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


def chat():

    isExist = os.path.exists("/lab/texts/discord")
    if isExist:
        shutil.rmtree("/lab/texts/discord")

    os.makedirs("/lab/texts/discord")

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
                            if str(i["author"]["id"]) == "975174695399854150":
                                print("allowing Eliza")
                            else:
                                continue

                        txt_file = open("/lab/texts/discord/" + filename + ".txt", "a")

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
                                        r"http\S+", "[REDACTED]", result["content"]
                                    )
                                    if len(result["mentions"]) > 0:
                                        for mention in result["mentions"]:
                                            sanitized = sanitized.replace(
                                                mention["name"],
                                                "<@" + str(mention["id"]) + ">",
                                            )
                                    content = result["author"]["id"] + ": " + sanitized
                                    txt_file.write(f"{content}\n".format(content))
                            except Exception as e:
                                print(e)
                                print("failed to prepare a reply")

                        try:
                            sanitized = re.sub(r"http\S+", "[REDACTED]", i["content"])
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        mention["name"], "<@" + str(mention["id"]) + ">"
                                    )

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


chat()
read()
