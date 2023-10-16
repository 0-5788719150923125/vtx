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
                    f"{root_dir}/train/{sub}/submissions/" + submission.id + ".txt", "a"
                ) as file:
                    file.write(f"## RECORD\n---\n```\n")
                    file.write(f"submission.id: {submission.id}\n")
                    file.write(f"submission.created: {submission.created_utc}\n")
                    file.write(f"submission.title: {submission.title}\n")
                    file.write(f"submission.subreddit: /r/{submission.subreddit}\n")
                    author = submission.author
                    if author:
                        if author.name in config["reddit"]["replacers"]:
                            author = config["reddit"]["replacers"][author.name]
                    file.write(f"submission.author: {author}\n")
                    file.write(f"submission.score: {submission.score}\n")
                    file.write(
                        f"submission.permalink: https://reddit.com{submission.permalink}\n"
                    )
                    if submission.selftext != "":
                        file.write("```\n\n## ECO\n---\n")
                        sanitized = re.sub(
                            r"http\S+",
                            "((url))",
                            submission.selftext.replace("\n", "\\n"),
                        )
                        file.write(sanitized)
                    else:
                        file.write("```\n\n## TRIGGER\n---\n")
                        file.write(f"[((({get_identity()})))]({submission.url})")

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
                    f"{root_dir}/train/{sub}/comments/" + reply.id + ".txt",
                    "a",
                ) as file:
                    context.append(reply)

                    file.write(f"## RECORD\n---\n```\n")
                    file.write(f"reply.id: {reply.id}\n")
                    file.write(f"reply.created: {reply.created_utc}\n")
                    file.write(f"reply.parent_id: {reply.parent_id}\n")
                    author = reply.author
                    if author:
                        if author.name in config["reddit"]["replacers"]:
                            author = config["reddit"]["replacers"][author.name]
                    props = [
                        f"reply.score: {reply.score}\n",
                        f"reply.author: {author}\n",
                    ]
                    random.shuffle(props)
                    file.write(props[0])
                    file.write(props[1])
                    file.write(
                        f"reply.permalink: https://reddit.com{reply.permalink}\n"
                    )
                    file.write("```\n\n## ECO\n---\n")
                    sanitized = re.sub(
                        r"http\S+",
                        "((url))",
                        reply.body.replace("\n", "\\n"),
                    )
                    file.write(sanitized)

                dump_replies(reply.replies, submission, context)
                context.pop()

        dump_submissions()


if __name__ == "__main__":
    main()
