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

import jsonlines
import praw
import requests
from bs4 import BeautifulSoup

from common import config, get_identity, get_past_datetime, ship, wall


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


# def fetch_from_matrix():
#     client = AsyncClient("https://matrix.org", os.environ["MATRIXUSER"])

#     async def iterate():
#         await client.login(os.environ["MATRIXPASSWORD"])

#         room_id = "!apmkrFyPwFRRvQgtEw:gitter.im"

#         # Initialize pagination
#         start_token = "$NQ04ubhtjsFD-pKKa4EX3uHm63K1afauqWpbTes_F0w"
#         while True:
#             try:
#                 response = await client.room_messages(
#                     room_id, limit=10, start=start_token
#                 )
#                 print(response)
#                 if not response or not response.get("chunk"):
#                     break

#                 for event in response["chunk"]:
#                     if event["type"] == "m.room.message":
#                         content = event["content"]
#                         sender = event["sender"]
#                         message_body = content["body"]

#                         print(f"Message from {sender}: {message_body}")

#                 # Get the token for the next page of events
#                 start_token = response.get("end")
#                 if not start_token:
#                     break

#             except Exception as e:
#                 logging.error(e)
#                 break

#         await client.sync_forever(timeout=30000, full_state=True)

#     asyncio.run(iterate())


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
    if not os.path.exists("/data/discord"):
        os.makedirs("/data/discord")

    # Export direct messages
    if config["discord"]["export_dms"] == True:
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportdm -t "{discord_token}" -o "/data/discord/dm-%c.json" -f "JSON"'
        os.system(command)

    # For every server listed in config, iterate over options, and download messages
    for server in config["discord"]["servers"]:
        print("exporting " + str(server))

        skip = False
        s = config["discord"]["servers"][server]
        command = f'dotnet /usr/share/dce/DiscordChatExporter.Cli.dll exportguild --guild "{str(server)}" -t "{discord_token}" -o "/data/discord/g-%g-%c.json" -f "JSON"'
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
        for filename in os.listdir("/data/discord"):
            if filename.startswith(f"g-{str(server)}"):
                os.remove(os.path.join("/data/discord", filename))
        os.system(command)


# Replace unapproved bots with random IDs, so as not to bias the model toward poor outputs
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
            "((url))",
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

    successes = 0
    failures = 0
    for filename in os.listdir("/data/discord"):
        try:
            with open(os.path.join("/data/discord", filename), "r") as file:
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
                                i["content"] + " | ((" + i["embeds"][0]["title"] + "))"
                            )
                        if i["embeds"][0]["description"]:
                            i["content"] = (
                                i["content"]
                                + " | (("
                                + i["embeds"][0]["description"]
                                + "))"
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
                                                    + " | (("
                                                    + result["embeds"][0]["title"]
                                                    + "))"
                                                )
                                            if result["embeds"][0]["description"]:
                                                result["content"] = (
                                                    result["content"]
                                                    + " | (("
                                                    + result["embeds"][0]["description"]
                                                    + "))"
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
                                            wall
                                            + reply_author_id
                                            + ship
                                            + " "
                                            + sanitized
                                        )
                                        txt_file.write(f"{content}\n".format(content))
                                        successes += 1
                            except Exception as e:
                                failures += 1

                        try:
                            sanitized = sanitizer(i["content"])
                            if len(i["mentions"]) > 0:
                                for mention in i["mentions"]:
                                    sanitized = sanitized.replace(
                                        "@" + mention["nickname"],
                                        "<@" + str(mention["id"]) + ">",
                                    )
                            sanitized = transform_message(sanitized)
                            content = wall + author_id + ship + " " + sanitized
                            txt_file.write(f"{content}\n".format(content))
                            successes += 1
                        except Exception as e:
                            failures += 1
        except Exception as e:
            failures += 1

        os.system("clear")
        print("preparing Discord messages")
        print(f"{successes} successes, {failures} failures")


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
                total = total + 1
                os.system("clear")
                print("archiving /r/" + sub)
                print("archived " + str(total) + " submissions")

                dump_replies(
                    replies=submission.comments,
                    submission=submission,
                    context=["default"],
                )

        def dump_replies(replies, submission, context=[]):
            for reply in replies:
                with open(
                    "/lab/reddit/" + sub + "/" + reply.submission.id + ".txt", "a"
                ) as file:
                    if isinstance(reply, praw.models.MoreComments):
                        continue

                    context[0] = submission
                    context.append(reply)

                    for line in context:
                        if getattr(line, "title", None) is not None:
                            bias = get_identity()
                            author = line.author
                            if author:
                                if author.name in config["reddit"]["replacers"]:
                                    bias = config["reddit"]["replacers"][author.name]
                            original_submission = (
                                wall + str(bias) + ship + " ((" + line.title + "))"
                            )
                            if line.selftext:
                                original_submission = (
                                    original_submission
                                    + " | "
                                    + line.selftext.replace("\n", "\\n")
                                )
                            sanitized = re.sub(
                                r"http\S+",
                                "((url))",
                                original_submission,
                            )
                            file.write(sanitized + " ")
                            continue
                        bias = get_identity()
                        author = line.author
                        if author:
                            if author.name in config["reddit"]["replacers"]:
                                bias = config["reddit"]["replacers"][author.name]

                        sanitized = re.sub(
                            r"http\S+",
                            "((url))",
                            wall
                            + str(bias)
                            + ship
                            + " "
                            + line.body.replace("\n", "\\n"),
                        )
                        file.write(sanitized + " ")
                    file.write("\n")

                dump_replies(reply.replies, submission, context)
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
        agents = get_random_samples(10000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open("/lab/juxtaposition/0/" + "mirror.csv", "w", newline="") as file:
        agents = get_samples(10000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        csvwriter.writerows(agents[1:])

    with open(
        "/lab/juxtaposition/0/" + "left-sorted-mirror.csv", "w", newline=""
    ) as file:
        agents = get_samples(10000)
        csvwriter = csv.writer(file)
        csvwriter.writerow(["agent", "bot"])
        sorted_list = sorted(agents, key=lambda x: int(x[0]), reverse=False)
        csvwriter.writerows(sorted_list)

    with open(
        "/lab/juxtaposition/0/" + "right-sorted-mirror.csv", "w", newline=""
    ) as file:
        agents = get_samples(10000)
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
        count = 3333
        while i < count:
            sequence = random_fibonacci_list(23)
            if random.random() < 0.5:
                sequence.reverse()
            numbers.append(sequence)
            i = i + 1
        csvwriter.writerows(numbers)


def create_instructions():
    if os.path.exists("/lab/instruct/natural"):
        shutil.rmtree("/lab/instruct/natural")
    if not os.path.exists("/lab/instruct/natural"):
        os.makedirs("/lab/instruct/natural")
    with jsonlines.open("/lab/instruct/unnatural/full_data.jsonl") as f:
        instance = 0
        for line in f.iter():
            instance = instance + 1
            # if instance > 1000:
            #     return
            with open(
                "/lab/instruct/natural/" + f"instruction-{instance}a.md",
                "a",
                newline="",
            ) as file:
                # pprint(line)
                file.write("## INSTRUCTION\n---\n")
                file.write(line["instruction"] + "\n\n")
                if not line["instances"][0]["input"].startswith("None"):
                    file.write("## INPUT\n---\n")
                    file.write(line["instances"][0]["input"] + "\n\n")
                if "reformulations" in line:
                    file.write("## ECHO\n---\n")
                    file.write(line["reformulations"][0]["instruction"] + "\n\n")
                if "constraints" in line["instances"][0]:
                    if (
                        not line["instances"][0]["constraints"]
                        .lower()
                        .startswith("none")
                    ):
                        word = random.choice(
                            ["CONSTRAINTS", "LAW", "RULE", "DEMAND", "ACTION"]
                        )
                        file.write(f"## {word}\n---\n")
                        file.write(line["instances"][0]["constraints"] + "\n\n")
                if not line["instances"][0]["output"].startswith("None"):
                    file.write("## OUTPUT\n---\n")
                    file.write(line["instances"][0]["output"] + "\n\n")
            if "reformulations" in line:
                with open(
                    "/lab/instruct/natural/" + f"instruction-{instance}b.md",
                    "a",
                    newline="",
                ) as file:
                    file.write("## INSTRUCTION\n---\n")
                    file.write(line["reformulations"][0]["instruction"] + "\n\n")
                    if not line["reformulations"][0]["input"].startswith("None"):
                        file.write("## INPUT\n---\n")
                        file.write(line["reformulations"][0]["input"] + "\n\n")
                    if not line["reformulations"][0]["output"].startswith("None"):
                        file.write("## OUTPUT\n---\n")
                        file.write(line["reformulations"][0]["output"] + "\n\n")
                if len(line["reformulations"]) > 1:
                    with open(
                        "/lab/instruct/natural/" + f"instruction-{instance}c.md",
                        "a",
                        newline="",
                    ) as file:
                        file.write("## INSTRUCTION\n---\n")
                        file.write(line["reformulations"][1]["instruction"] + "\n\n")
                        if not line["reformulations"][1]["input"].startswith("None"):
                            file.write(f"## INPUT\n---\n")
                            file.write(line["reformulations"][1]["input"] + "\n\n")
                        if not line["reformulations"][1]["output"].startswith("None"):
                            file.write("## OUTPUT\n---\n")
                            file.write(line["reformulations"][1]["output"] + "\n\n")
            # with open(
            #     "/lab/instruct/natural/" + f"instruction-{instance}a.md",
            #     "a",
            #     newline="",
            # ) as file:
            #     # pprint(line)
            #     if not line["instances"][0]["input"].startswith("None"):
            #         file.write("## TRIGGER\n---\n")
            #         file.write(line["instances"][0]["input"] + "\n\n")
            #     file.write("## ECO\n---\n")
            #     file.write(line["instruction"] + "\n\n")
            #     if "reformulations" in line:
            #         file.write("## ECHO\n---\n")
            #         file.write(line["reformulations"][0]["instruction"] + "\n\n")
            #     if "constraints" in line["instances"][0]:
            #         if (
            #             not line["instances"][0]["constraints"]
            #             .lower()
            #             .startswith("none")
            #         ):
            #             word = random.choice(
            #                 ["CONSTRAINTS", "LAW", "RULE", "DEMAND", "ACTION"]
            #             )
            #             file.write(f"## {word}\n---\n")
            #             file.write(line["instances"][0]["constraints"] + "\n\n")
            #     if not line["instances"][0]["output"].startswith("None"):
            #         file.write("## PREDICTION\n---\n")
            #         file.write(line["instances"][0]["output"] + "\n\n")
            # if "reformulations" in line:
            #     with open(
            #         "/lab/instruct/natural/" + f"instruction-{instance}b.md",
            #         "a",
            #         newline="",
            #     ) as file:
            #         if not line["reformulations"][0]["input"].startswith("None"):
            #             file.write("## TRIGGER\n---\n")
            #             file.write(line["reformulations"][0]["input"] + "\n\n")
            #         file.write("## ECO\n---\n")
            #         file.write(line["reformulations"][0]["instruction"] + "\n\n")
            #         if not line["reformulations"][0]["output"].startswith("None"):
            #             file.write("## PREDICTION\n---\n")
            #             file.write(line["reformulations"][0]["output"] + "\n\n")
            #     if len(line["reformulations"]) > 1:
            #         with open(
            #             "/lab/instruct/natural/" + f"instruction-{instance}c.md",
            #             "a",
            #             newline="",
            #         ) as file:
            #             if not line["reformulations"][1]["input"].startswith("None"):
            #                 word = random.choice(["TRIGGER", "SIGNAL", "EVENT"])
            #                 file.write(f"## {word}\n---\n")
            #                 file.write(line["reformulations"][1]["input"] + "\n\n")
            #             file.write("## ECO\n---\n")
            #             file.write(line["reformulations"][1]["instruction"] + "\n\n")
            #             if not line["reformulations"][1]["output"].startswith("None"):
            #                 file.write("## PREDICTION\n---\n")
            #                 file.write(line["reformulations"][1]["output"] + "\n\n")


def create_logic():
    if os.path.exists("/lab/logic/train"):
        shutil.rmtree("/lab/logic/train")
    if not os.path.exists("/lab/logic/train"):
        os.makedirs("/lab/logic/train")
    with open("/lab/logic/AND.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"/lab/logic/train/AND{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["and", "AND", "&&"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")

    with open("/lab/logic/IMPLICATION.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(
                f"/lab/logic/train/IMPLICATION{line[0]}.txt", "w", newline=""
            ) as file:
                file.write(
                    f"if {line[2]} is sufficient for {line[1]}, then {line[1]} implies {line[2]} is {line[3]}"
                )

    with open("/lab/logic/NOT.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"/lab/logic/train/NOT{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["is not", "is NOT", "!="])
                file.write(f"if X1 is {line[1]}, then Target {operator} {line[2]}")

    with open("/lab/logic/OR.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"/lab/logic/train/OR{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["or", "OR", "||"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")

    with open("/lab/logic/XOR.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"/lab/logic/train/XOR{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["xor", "XOR", "exclusive or"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")
