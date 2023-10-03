import asyncio
import logging
import os
import random
import time

import tweepy

import head
from common import ad, bc


def main(config):
    asyncio.run(loop(config["twitter"]))


if __name__ == "main":
    main(config)


async def loop(config):
    while True:
        if random.random() < config.get("frequency", 0.001):
            topics = config.get("topics", ["AI alignment"])
            output = await head.ctx.prompt(
                prompt=random.choice(topics),
                min_new_tokens=11,
                max_new_tokens=56,
                ideas=config.get("ideas", None),
                # decay_after_length=6,
                # decay_factor=2.3,
                eos_tokens=[".", "?", "!", "\n", "\n\n", "\\"],
                cleanup=True,
            )
            if output == False:
                continue
            print(bc.CORE + "ONE@TWITTER: " + ad.TEXT + output)
            try:
                await tweet(output)
            except Exception as e:
                logging.error(e)
        time.sleep(66.6)


async def tweet(message: str = "This is an automated test."):
    client = tweepy.Client(bearer_token=os.environ["TWITTERBEARERTOKEN"])

    client = tweepy.Client(
        consumer_key=os.environ["TWITTERCONSUMERKEY"],
        consumer_secret=os.environ["TWITTERCONSUMERSECRET"],
        access_token=os.environ["TWITTERACCESSTOKEN"],
        access_token_secret=os.environ["TWITTERACCESSTOKENSECRET"],
    )
    response = client.create_tweet(text=message)
