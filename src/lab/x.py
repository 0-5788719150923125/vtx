import asyncio
import logging
import os
import random
import time

import tweepy

import head
from common import colors


def main(config):
    asyncio.run(loop(config["x"]))


if __name__ == "main":
    main(config)


async def loop(config):
    while True:
        if random.random() < config.get("frequency", 0.001):
            topics = config.get("topics", ["AI alignment"])
            output = await head.ctx.prompt(
                prompt=random.choice(topics),
                min_new_tokens=16,
                max_new_tokens=56,
                disposition=config.get("disposition", None),
                eos_tokens=[".", "?", "!", "\n", "\n\n", "\\", '"'],
                cleanup=True,
            )
            if output == False:
                continue
            print(colors.RED + "ONE@X: " + colors.WHITE + output)
            try:
                await tweet(output)
            except Exception as e:
                logging.error(e)
        time.sleep(66.6)


async def tweet(message: str = "This is an automated test."):
    client = tweepy.Client(bearer_token=os.environ["XBEARERTOKEN"])

    client = tweepy.Client(
        consumer_key=os.environ["XCONSUMERKEY"],
        consumer_secret=os.environ["XCONSUMERSECRET"],
        access_token=os.environ["XACCESSTOKEN"],
        access_token_secret=os.environ["XACCESSTOKENSECRET"],
    )
    response = client.create_tweet(text=message)
