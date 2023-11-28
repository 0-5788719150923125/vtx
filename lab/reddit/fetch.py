import os
import random
import re
import shutil
import sys
from datetime import datetime

sys.path.append("/src")

import praw

from common import config, get_identity, ship, wall

root_dir = "/lab/reddit"


# Download messages from subreddits
def main():
    # Instantiate the Reddit client
    reddit = praw.Reddit(
        client_id=os.environ["REDDITCLIENT"],
        client_secret=os.environ["REDDITSECRET"],
        user_agent=os.environ["REDDITAGENT"],
    )

    # For every sub in config, iterate over options, then download content
    for sub in config["reddit"]["subs"]:
        skip = False
        opts = config["reddit"]["subs"][sub]
        if sub == "prompt":
            continue

        sort = "top"
        limit = 5
        if opts is not None:
            skip = opts.get("skip", False)
            limit = opts.get("limit", limit)
            sort = opts.get("sort", sort)

        if skip == True:
            continue

        # Ensure path exists and is empty
        if os.path.exists(f"{root_dir}/train/{sub}"):
            shutil.rmtree(f"{root_dir}/train/{sub}")

        os.makedirs(f"{root_dir}/train/{sub}/submissions")
        os.makedirs(f"{root_dir}/train/{sub}/comments")

        identities = {}

        def dump_submissions():
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

                with open(
                    f"{root_dir}/train/{sub}/submissions/" + submission.id + ".md", "a"
                ) as file:
                    file.write("```\n")
                    if random.random() > 0.5:
                        created = datetime.utcfromtimestamp(
                            submission.created_utc
                        ).strftime("%Y-%m-%d @ %H:%M")
                    else:
                        created = submission.created_utc

                    s_variant = random.choice(["submission", "s"])
                    props = [
                        f"{s_variant}.id: {submission.id}\n",
                        f"{s_variant}.created: {created}\n",
                        f"{s_variant}.title: {submission.title}\n",
                        f"{s_variant}.subreddit: /r/{submission.subreddit}\n",
                        f"{s_variant}.score: {submission.score}\n",
                        f"{s_variant}.permalink: https://reddit.com{submission.permalink}\n",
                    ]

                    author = submission.author
                    if author is not None:
                        props.append(f"{s_variant}.author: {author}\n")
                        author_id = get_identity(author)
                        if author.name in config["reddit"].get("replacers", {}):
                            author_id = config["reddit"]["replacers"][author.name]
                        props.append(f"{s_variant}.author.id: {author_id}\n")

                    if submission.selftext != "":
                        sanitized = re.sub(
                            r"http\S+",
                            "((url))",
                            submission.selftext,
                        )
                        props.append(f"{s_variant}.text: " + sanitized + "\n")
                    else:
                        props.append(f"{s_variant}.image: {submission.url}" + "\n")

                    random.shuffle(props)
                    for prop in props:
                        file.write(prop)
                    file.write("```")

                dump_replies(
                    replies=submission.comments,
                    submission=submission,
                    context=["default"],
                )

        def dump_replies(replies, submission, context=[]):
            for reply in replies:
                if isinstance(reply, praw.models.MoreComments):
                    continue

                with open(
                    f"{root_dir}/train/{sub}/comments/" + reply.id + ".md",
                    "a",
                ) as file:
                    context.append(reply)

                    if random.random() > 0.5:
                        created = datetime.utcfromtimestamp(reply.created_utc).strftime(
                            "%Y-%m-%d @ %H:%M"
                        )
                    else:
                        created = submission.created_utc

                    file.write("```\n")
                    c_variant = random.choice(["comment", "reply", "c", "r"])
                    props = [
                        f"{c_variant}.id: {reply.id}\n",
                        f"{c_variant}.created: {created}\n",
                        f"{c_variant}.parent.id: {reply.parent_id}\n",
                        f"{c_variant}.score: {reply.score}\n",
                        f"{c_variant}.permalink: https://reddit.com{reply.permalink}\n",
                    ]

                    author = reply.author
                    if author is not None:
                        props.append(f"{c_variant}.author: {author}\n")
                        author_id = get_identity(author)
                        if author.name in config["reddit"].get("replacers", {}):
                            author_id = config["reddit"]["replacers"][author.name]
                        props.append(f"{c_variant}.author.id: {author_id}\n")

                    sanitized = re.sub(
                        r"http\S+",
                        "((url))",
                        f"{c_variant}.text: " + reply.body,
                    )
                    props.append(sanitized + "\n")

                    random.shuffle(props)

                    for prop in props:
                        file.write(prop)

                    file.write("```")

                dump_replies(reply.replies, submission, context)
                context.pop()

        dump_submissions()


if __name__ == "__main__":
    main()
