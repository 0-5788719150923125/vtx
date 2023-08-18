import os
import random
import tweepy
from utils import ad, bc


async def orchestrate(config):
    if random.random() < 0.00059:
        topics = config.get("topics", ["AI alignment"])
        task = loop.create_task(
            lab.twitter.send(
                await head.gen(
                    prefix=random.choice(topics),
                    max_new_tokens=63,
                    decay_after_length=6,
                    decay_factor=0.0023,
                    mode="prompt",
                )
            )
        )


async def send(message: str = "This is an automated test."):
    client = tweepy.Client(bearer_token=os.environ["TWITTERBEARERTOKEN"])

    client = tweepy.Client(
        consumer_key=os.environ["TWITTERCONSUMERKEY"],
        consumer_secret=os.environ["TWITTERCONSUMERSECRET"],
        access_token=os.environ["TWITTERACCESSTOKEN"],
        access_token_secret=os.environ["TWITTERACCESSTOKENSECRET"],
    )
    response = client.create_tweet(text=message)
    print(bc.CORE + "ONE@TWITTER: " + ad.TEXT + message)
