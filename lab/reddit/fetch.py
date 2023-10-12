import os
import random
import re
import shutil
import sys

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

        os.makedirs(f"{root_dir}/train/{sub}")

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

                dump_replies(
                    replies=submission.comments,
                    submission=submission,
                    context=["default"],
                )

        def dump_replies(replies, submission, context=[]):
            for reply in replies:
                with open(
                    f"{root_dir}/train/{sub}/" + reply.submission.id + ".txt", "a"
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

        dump_submissions()


if __name__ == "__main__":
    main()
