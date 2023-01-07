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
    for filename in os.listdir(home):
        try:
            # open in readonly mode
            with open(os.path.join(home, filename), "r") as file:
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
    guild = str(829345498326106142)

    async for sub in subreddit.hot(limit=100):
        try:
            await save_message(guild + ": " + sub.title)
            await save_message(guild + ": " + sub.selftext)
        except:
            print("fail")


async def read():
    print("reading markdown files")
    files = glob.glob("/lab/ink" + "/**/*.md", recursive=True)
    for filename in files:
        try:
            with open(os.path.join("/lab/ink", filename), "r") as file:
                txt = open(output_file, "a")
                txt.write(f"806051627198709760:\n")
                txt.writelines(file.readlines())
                txt.close()
                file.close()
        except:
            print("something failed while reading markdown files")


async def translate():
    print("beginning translation")
    files = glob.glob("/lab/research" + "/**/*.txt", recursive=True)
    for filename in files:
        try:
            with open(os.path.join("/lab/research", filename), "r") as file:
                txt = open(output_file, "a")
                txt.write(f"832310224303161364:\n")
                txt.writelines(file.readlines())
                txt.close()
                file.close()
        except:
            print("something failed while eating a research file")


async def save_message(output):
    txt = open(output_file, "a")
    txt.write(f"{output}\n".format(output))
    txt.close()
