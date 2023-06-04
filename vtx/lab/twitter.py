import os
import tweepy
from utils import ad, bc

client = tweepy.Client(bearer_token=os.environ["TWITTERBEARERTOKEN"])

client = tweepy.Client(
    consumer_key=os.environ["TWITTERCONSUMERKEY"],
    consumer_secret=os.environ["TWITTERCONSUMERSECRET"],
    access_token=os.environ["TWITTERACCESSTOKEN"],
    access_token_secret=os.environ["TWITTERACCESSTOKENSECRET"],
)


async def send(message: str = "This is an automated test."):
    global client
    response = client.create_tweet(text=message)
    print(bc.CORE + "ONE@TWITTER: " + ad.TEXT + message)
