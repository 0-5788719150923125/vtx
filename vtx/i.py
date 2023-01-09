import os
import json
import re
import glob
import asyncpraw as praw

home = "/lab"
output_file = "./input.txt"


def spy():
    print("a noun")


def integrate():
    print("sight and sound")


def vision():
    print("a view through my lens")


async def feed():

    if os.path.exists(output_file):
        os.remove(output_file)

    print("tried to eat Discord exports")
    for filename in os.listdir("/lab/texts/discord"):
        try:
            with open(os.path.join("/lab/texts/discord", filename), "r") as file:
                try:
                    data = json.load(file)

                    for i in data["messages"]:
                        if i["type"] != "Default" and i["type"] != "Reply":
                            continue
                        if i["content"] == "":
                            continue

                        txt_file = open(output_file, "a")

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


async def scrape():
    print("scrape reddit")
    dread = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )
    subreddit = await dread.subreddit("stairsofpantheon", fetch=True)

    async for sub in subreddit.hot(limit=100):
        try:
            txt = open(output_file, "a")
            txt.write(sub.title)
            txt.write(sub.selftext)
            txt.close()
        except:
            print("fail")


async def read():

    print("reading markdown from the lab")
    files = glob.glob("/lab" + "/**/*.md", recursive=True)
    for filename in files:
        try:
            with open(os.path.join("/lab", filename), "r") as file:
                txt = open(output_file, "a")
                txt.write(f"\n\n")
                txt.writelines(file.readlines())
                txt.close()
                file.close()
        except:
            print("something failed while reading markdown entries")

    print("reading txt files from the lab")
    files = glob.glob("/lab" + "/**/*.txt", recursive=True)
    for filename in files:
        try:
            with open(os.path.join("/lab", filename), "r") as file:
                txt = open(output_file, "a")
                txt.write(f"\n\n")
                txt.writelines(file.readlines())
                txt.close()
                file.close()
        except:
            print("something failed while reading txt entries")
    print("done")
