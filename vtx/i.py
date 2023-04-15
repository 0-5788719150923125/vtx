import requests
import secrets
import shutil
import random
import json
import csv
import os
from utils import config, get_identity, propulsion, ship
from bs4 import BeautifulSoup
from pprint import pprint
import re
import praw
import numpy as np
import math

# Grab all internal links from a web page
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


# Fetch messages from Discord, by using Discord Chat Exporter
def fetch_from_discord():

    # By default, use the bot's token
    discord_token = os.environ["DISCORDTOKEN"]

    # If a self token is specific, use that
    if "use_self_token" in config["discord"]:
        if config["discord"]["use_self_token"] == True:
            discord_token = os.environ["SELFTOKEN"]

    # Ensure directory has been created
    if not os.path.exists("/gen/discord"):
        os.makedirs("/gen/discord")

    # Export direct messages
    if config["discord"]["export_dms"] == True:
        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "/gen/discord" -f "JSON"'
        os.system(command)

    # For every server listed in config, iterate over options, and download messages
    for server in config["discord"]["servers"]:
        print("exporting " + server)
        skip = False
        try:
            skip = config["discord"]["servers"][server].get("skip", False)
        except:
            skip = False
        if skip == True:
            continue

        command = f'dotnet /dce/DiscordChatExporter.Cli.dll exportguild --guild "{server}" -t "{discord_token}" -o "/gen/discord" -f "JSON"'
        if "before" in server:
            command.join(" --before " + server["before"])
        if "after" in server:
            command.join(" --after " + server["after"])
        os.system(command)


# Replace approved bots with random IDs, so as not to bias the model toward poor outputs
def transform_author(author):
    if str(author["id"]) == "975174695399854150":  # Eliza
        return str(author["id"])
    elif str(author["id"]) == "1055993037077106718":  # Samn
        return str(get_identity())
    elif "Ghost-" in author["name"]:
        return str(get_identity())
    else:
        return False


# Replace third person messaging from bots, so as not to bias the model towards this format
def transform_message(message):
    matchers = [
        r'(?:The ghost of )(?:<@\d*>)(?: suggests, \*")(.*)(?:"\*$)',
        r'(?:<@\d*>)(?: says, \*")(.*)(?:"\*$)',
        r'(?:<@\d*>)(?: would say, \*")(.*)(?:"\*$)',
        r'(?:They said, \*")(.*)(?:"\*$)',
    ]
    for pattern in matchers:
        matcher = re.compile(pattern)
        if matcher.match(message):
            group = re.search(matcher, message)
            message = group[1]
            break
    return message


# Format Discord messages for training
def prepare_discord_messages():

    # Replace links and @mentions
    def sanitizer(string):
        sanitized = re.sub(
            r"http\S+",
            f"((({str(get_identity())})))",
            string,
        )
        sanitized = re.sub(
            r"@Unknown",
            "<@" + str(get_identity()) + ">",
            sanitized,
        )
        return sanitized

    # Ensure export path exists and is clean
    if os.path.exists("/lab/discord/exported"):
        shutil.rmtree("/lab/discord/exported")

    os.makedirs("/lab/discord/exported")

    print("preparing Discord messages")
    for filename in os.listdir("/gen/discord"):
        try:
            with open(os.path.join("/gen/discord", filename), "r") as file:
                data = json.load(file)

                for i in data["messages"]:

                    if i["type"] != "Default" and i["type"] != "Reply":
                        continue

                    if len(i["embeds"]) > 0:
                        if i["content"] != "":
                            i["content"] = i["content"]
                        if i["embeds"][0]["title"]:
                            i["content"] = (
                                i["content"] + " | " + i["embeds"][0]["title"]
                            )
                        if i["embeds"][0]["description"]:
                            i["content"] = (
                                i["content"] + " | " + i["embeds"][0]["description"]
                            )

                    author_id = i["author"]["id"]

                    if i["author"]["isBot"] == True:
                        author_id = transform_author(i["author"])
                        if author_id == False:
                            continue

                    with open(
                        "/lab/discord/exported/" + filename + ".txt", "a"
                    ) as txt_file:

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

                                reply_author_id = result["author"]["id"]

                                if result["author"]["isBot"] == True:
                                    reply_author_id = transform_author(result["author"])

                                if reply_author_id != False:
                                    if result is not None:
                                        if len(result["embeds"]) > 0:
                                            if result["content"] != "":
                                                result["content"] = result["content"]
                                            if result["embeds"][0]["title"]:
                                                result["content"] = (
                                                    result["content"]
                                                    + " | "
                                                    + result["embeds"][0]["title"]
                                                )
                                            if result["embeds"][0]["description"]:
                                                result["content"] = (
                                                    result["content"]
                                                    + " | "
                                                    + result["embeds"][0]["description"]
                                                )
                                        sanitized = sanitizer(result["content"])
                                        if len(result["mentions"]) > 0:
                                            for mention in result["mentions"]:
                                                sanitized = sanitized.replace(
                                                    "@" + mention["name"],
                                                    "<@" + str(mention["id"]) + ">",
                                                )
                                        sanitized = transform_message(sanitized)
                                        content = (
                                            propulsion
                                            + reply_author_id
                                            + ship
                                            + " "
                                            + sanitized
                                        )
                                        txt_file.write(f"{content}\n".format(content))
                            except Exception as e:
                                print(e)
                                print("failed to prepare a reply")

                        try:
                            sanitized = sanitizer(i["content"])
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        "@" + mention["name"],
                                        "<@" + str(mention["id"]) + ">",
                                    )
                            sanitized = transform_message(sanitized)
                            content = propulsion + author_id + ship + " " + sanitized
                            txt_file.write(f"{content}\n".format(content))
                        except Exception as e:
                            print(e)
                            print("Failed: " + i["id"])

        except Exception as e:
            print(e)


# Download messages from subreddits
def fetch_from_reddit():

    # Instantiate the Reddit client
    reddit = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )

    # For every sub in config, iterate over options, then download content
    for sub in config["reddit"]:

        skip = False
        if "skip" in config["reddit"][sub]:
            skip = config["reddit"][sub]["skip"]

        limit = 50
        if "limit" in config["reddit"][sub]:
            limit = config["reddit"][sub]["limit"]

        if skip == True:
            continue
        else:
            print("archiving " + sub)

        # Ensure path exists and is empty
        if os.path.exists("/lab/reddit/" + sub):
            shutil.rmtree("/lab/reddit/" + sub)

        os.makedirs("/lab/reddit/" + sub)

        identities = {}

        sort = config["reddit"][sub].get("sort", "top")

        def main():

            if sort == "new":
                submissions = reddit.subreddit(sub).new(limit=limit)
            else:
                submissions = reddit.subreddit(sub).top(limit=limit)

            for submission in submissions:

                bias = get_identity()
                print("wrote to " + str(bias))

                context = []
                with open(
                    "/lab/reddit/" + sub + "/" + submission.id + ".txt", "a"
                ) as file:
                    sanitized = re.sub(
                        r"http\S+",
                        f"((({str(get_identity())})))",
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
                    "/lab/reddit/" + sub + "/" + reply.submission.id + ".txt", "a"
                ) as file:
                    sanitized = re.sub(
                        r"http\S+",
                        f"((({str(get_identity())})))",
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


# Create some structure
def get_juxtaposition_data():

    # Ensure path exists and is empty
    if os.path.exists("/lab/juxtaposition"):
        shutil.rmtree("/lab/juxtaposition")

    os.makedirs("/lab/juxtaposition/0")
    os.makedirs("/lab/juxtaposition/1")
    os.makedirs("/lab/juxtaposition/2")

    def get_samples(count):
        samples = []
        i = 0
        while i < count:
            block = get_identity()
            samples.append([block, block[::-1]])
            i = i + 1
        return samples

    with open("/lab/juxtaposition/0/" + "unsorted.csv", "w", newline="") as file:
        agents = get_samples(1500000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open("/lab/juxtaposition/0/" + "left-sorted.csv", "w", newline="") as file:
        agents = get_samples(1500000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[0]), reverse=False)
        csvwriter.writerows(sorted_list)

    with open("/lab/juxtaposition/0/" + "right-sorted.csv", "w", newline="") as file:
        agents = get_samples(1500000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[1]), reverse=True)
        csvwriter.writerows(sorted_list)

    def random_fibonacci_list(length):
        """
        Generates a list of Fibonacci numbers of the given length, starting at a random position in the Fibonacci sequence.
        """
        fibonacci_list = []
        a, b = 0, 1
        for i in range(random.randint(0, length)):
            # advance the Fibonacci sequence to a random position
            a, b = b, a + b
        fibonacci_list.append(a)
        fibonacci_list.append(b)
        for i in range(length - 2):
            # generate the next Fibonacci number by summing the previous two
            next_fibonacci = fibonacci_list[-1] + fibonacci_list[-2]
            fibonacci_list.append(next_fibonacci)
        return fibonacci_list

    with open("/lab/juxtaposition/2/" + "fibonacci.csv", "w", newline="") as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(
            [
                "one",
                "two",
                "three",
                "four",
                "five",
                "six",
                "seven",
                "eight",
                "nine",
                "ten",
                "eleven",
                "twelve",
                "thirteen",
                "fourteen",
                "fifteen",
                "sixteen",
                "seventeen",
                "eighteen",
                "nineteen",
                "twenty",
                "twenty-one",
                "twenty-two",
                "twenty-three",
            ]
        )
        i = 0
        numbers = []
        count = 33333
        while i < count:
            numbers.append(random_fibonacci_list(23))
            i = i + 1
        csvwriter.writerows(numbers)
