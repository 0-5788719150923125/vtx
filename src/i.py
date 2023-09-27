import asyncio
import csv
import json
import logging
import os
import random
import re
import shutil
import sys
from pprint import pprint

import praw
import requests
from bs4 import BeautifulSoup
from nio import AsyncClient, MatrixRoom, RoomMessage, RoomMessageText

from common import config, get_identity, get_past_datetime, propulsion, ship


def compile_book():
    command = f"hugo --source /book --noBuildLock"
    os.system(command)


def deploy_book():
    cloudflare_account_id = "a85a0cf89a8db6a8286fb4cba43558c2"
    project_name = "pen"
    command = f"WRANGLER_SEND_METRICS=true CLOUDFLARE_ACCOUNT_ID={cloudflare_account_id} wrangler pages deploy --project-name {project_name} --directory /book/public"
    os.system(command)


def convert_video_to_ascii():
    command = f"/src/scripts/mediatoascii --video-path /src/scripts/input.mp4 -o /src/scripts/output.mp4 --scale-down 16.0 --overwrite"
    os.system(command)


def upload_via_scp():
    command = f"scp -i /home/crow/Documents/creds/Oracle/one.key -r ./src/adapters/mind opc@129.159.66.224:/home/opc/vtx/src/adapters/mind"
    os.system(command)


def fetch_from_matrix():
    client = AsyncClient("https://matrix.org", os.environ["MATRIXUSER"])

    async def iterate():
        await client.login(os.environ["MATRIXPASSWORD"])

        room_id = "!apmkrFyPwFRRvQgtEw:gitter.im"

        # Initialize pagination
        start_token = "$NQ04ubhtjsFD-pKKa4EX3uHm63K1afauqWpbTes_F0w"
        while True:
            try:
                response = await client.room_messages(
                    room_id, limit=10, start=start_token
                )
                print(response)
                if not response or not response.get("chunk"):
                    break

                for event in response["chunk"]:
                    if event["type"] == "m.room.message":
                        content = event["content"]
                        sender = event["sender"]
                        message_body = content["body"]

                        print(f"Message from {sender}: {message_body}")

                # Get the token for the next page of events
                start_token = response.get("end")
                if not start_token:
                    break

            except Exception as e:
                logging.error(e)
                break

        await client.sync_forever(timeout=30000, full_state=True)

    asyncio.run(iterate())


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
            discord_token = os.environ["DISCORDSELFTOKEN"]

    # Ensure directory has been created
    if not os.path.exists("/gen/discord"):
        os.makedirs("/gen/discord")

    # Export direct messages
    if config["discord"]["export_dms"] == True:
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "/gen/discord/dm-%c.json" -f "JSON"'
        os.system(command)

    # For every server listed in config, iterate over options, and download messages
    for server in config["discord"]["servers"]:
        print("exporting " + str(server))
        skip = False
        s = config["discord"]["servers"][server]
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportguild --guild "{str(server)}" -t "{discord_token}" -o "/gen/discord/g-%g-%c.json" -f "JSON"'
        if s:
            if "skip" in s:
                skip = s.get("skip", False)
            if skip == True:
                continue
            if "before" in s:
                command = command + ' --before "' + s["before"] + '"'
            if "after" in s:
                command = command + ' --after "' + s["after"] + '"'
            if "past" in s:
                d = get_past_datetime(s["past"])
                command = command + f' --after "{str(d)}"'
        os.system(command)


# Replace approved bots with random IDs, so as not to bias the model toward poor outputs
def transform_author(author):
    if (
        str(author["id"]) == "975174695399854150"
        or str(author["id"]) == "315826602187554816"
        or str(author["id"]) == "1053270121218592798"
    ):  # Eliza, Kitsunetsuki, MAINNFRAME
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

                data_dict = {obj["id"]: obj for obj in data["messages"]}

                for i in data_dict.values():
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

                                result = data_dict.get(message_ref_id, None)

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
                                                    "@" + mention["nickname"],
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
                                logging.error(e)

                        try:
                            sanitized = sanitizer(i["content"])
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        "@" + mention["nickname"],
                                        "<@" + str(mention["id"]) + ">",
                                    )
                            sanitized = transform_message(sanitized)
                            content = propulsion + author_id + ship + " " + sanitized
                            txt_file.write(f"{content}\n".format(content))
                        except Exception as e:
                            logging.error(e)

        except Exception as e:
            logging.error(e)


# Download messages from subreddits
def fetch_from_reddit():
    # Instantiate the Reddit client
    reddit = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )

    # For every sub in config, iterate over options, then download content
    for sub in config["reddit"]["subs"]:
        skip = False
        if sub == "prompt":
            continue

        if "skip" in config["reddit"]["subs"][sub]:
            skip = config["reddit"]["subs"][sub]["skip"]

        limit = 5
        if "limit" in config["reddit"]["subs"][sub]:
            limit = config["reddit"]["subs"][sub]["limit"]

        if skip == True:
            continue

        # Ensure path exists and is empty
        if os.path.exists("/lab/reddit/" + sub):
            shutil.rmtree("/lab/reddit/" + sub)

        os.makedirs("/lab/reddit/" + sub)

        identities = {}

        sort = config["reddit"]["subs"][sub].get("sort", "top")

        def main():
            total = 0

            if sort == "new":
                submissions = reddit.subreddit(sub).new(limit=limit)
            else:
                submissions = reddit.subreddit(sub).top(limit=limit)

            for submission in submissions:
                bias = get_identity()
                total = total + 1
                os.system("clear")
                print("archiving /r/" + sub)
                print("archived " + str(total) + " submissions")

                author = submission.author
                if author:
                    if author.name in config["reddit"]["replacers"]:
                        bias = config["reddit"]["replacers"][author.name]

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

                with open(
                    "/lab/reddit/" + sub + "/" + reply.submission.id + ".txt", "a"
                ) as file:
                    bias = get_identity()
                    author = reply.author
                    if author:
                        if author.name in config["reddit"]["replacers"]:
                            bias = config["reddit"]["replacers"][author.name]

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
def juxtapose_data():
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

    def get_random_samples(count):
        samples = []
        i = 0
        while i < count:
            samples.append([get_identity(), get_identity()])
            i = i + 1
        return samples

    with open("/lab/juxtaposition/0/" + "random.csv", "w", newline="") as file:
        agents = get_random_samples(100000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open("/lab/juxtaposition/0/" + "mirror.csv", "w", newline="") as file:
        agents = get_samples(100000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open(
        "/lab/juxtaposition/0/" + "left-sorted-mirror.csv", "w", newline=""
    ) as file:
        agents = get_samples(100000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[0]), reverse=False)
        csvwriter.writerows(sorted_list)

    with open(
        "/lab/juxtaposition/0/" + "right-sorted-mirror.csv", "w", newline=""
    ) as file:
        agents = get_samples(100000)
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


def create_evil():
    with open("/lab/EVIL/" + "EVIL.csv", "w", newline="") as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(["in", "out"])
        evils = []
        for t in ["encoder", "decoder"]:
            for s in ["dev", "train", "test"]:
                l = open("/lab/EVIL/" + t + "-" + s + ".in", "r").read().split("\n")
                r = open("/lab/EVIL/" + t + "-" + s + ".out", "r").read().split("\n")
                for i, v in enumerate(l):
                    try:
                        evils.append([l[i], r[i]])
                    except Exception as e:
                        logging.error(e)
        csvwriter.writerows(evils)
