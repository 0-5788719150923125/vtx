import yaml
import praw, asyncpraw
from mergedeep import merge, Strategy
import asyncio
import os
import random
from twitter import *

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
        pprint.pprint(config)
except:
    config = default_config

token = os.environ["TWITTERAPIKEY"]
secret = os.environ["TWITTERAPISECRET"]
key = os.environ["TWITTERBEARERTOKEN"]

# oauth = Twitter.OAuth(token, secret, key)

# t = Twitter(auth=OAuth(token, secret, key, oauth))

# t.statuses.update(status="Hello, world!")
