import asyncio
import random
import tweepy
import os

# client = tweepy.Client(os.environ["TWITTERBEARERTOKEN"])

# auth = tweepy.OAuth2BearerHandler(os.environ["TWITTERBEARERTOKEN"])

# client = tweepy.Client(
#     consumer_key="API / Consumer Key here",
#     consumer_secret="API / Consumer Secret here",
#     access_token="Access Token here",
#     access_token_secret="Access Token Secret here",
# )

# api = tweepy.API(auth)

consumer_token = ""
consumer_secret = ""
access_token = ""
access_secret = ""

# auth = tweepy.OAuth2UserHandler(
#     client_id=client_id,
#     redirect_uri=redirect_uri,
#     scope=["tweet.read", "tweet.write", "users.read"],
#     client_secret=client_secret
# )

# auth = tweepy.OAuth2UserHandler(consumer_token, consumer_secret)

# session = tweepy.Client(
#     consumer_key=consumer_token,
#     consumer_secret=consumer_secret,
#     access_token=access_token,
#     access_token_secret=access_secret,
# )

# token = session.get("request_token")
# token = os.environ["TWITTERAPIKEY"]
# secret = os.environ["TWITTERAPISECRET"]

# auth = tweepy.OAuth1UserHandler(token, secret)

# api = tweepy.API(auth)

# print(auth.get_authorization_url(signin_with_twitter=True))


# public_tweets = api.home_timeline()
# for tweet in public_tweets:
#     print(tweet.text)

# token = os.environ["TWITTERAPIKEY"]
# secret = os.environ["TWITTERAPISECRET"]
# key = os.environ["TWITTERBEARERTOKEN"]

# oauth = Twitter.OAuth(token, secret, key)

# t = Twitter(auth=OAuth(token, secret, key, oauth))

# t.statuses.update(status="Hello, world!")
