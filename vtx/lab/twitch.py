from twitchAPI.twitch import Twitch
from twitchAPI.pubsub import PubSub
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
from twitchAPI import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatSub, ChatCommand
import asyncio
import os
import time
from utils import ad, bc, config, get_identity, propulsion, ship
import head
import lab.source
import random


# twitch token -u -s 'chat:read chat:edit channel:moderate'
async def subscribe():
    # initialize the twitch instance, this will by default also create a app authentication for you

    class TwitchBot:
        def __init__(self, client_id, client_secret, oauth_token, username, channel):
            self.client_id = client_id
            self.client_secret = client_secret
            self.oauth_token = oauth_token
            self.username = username
            self.channel = channel
            self.twitch = Twitch(client_id, client_secret)
            self.pubsub = PubSub(self.twitch)

        # this is where we set up the bot
        async def listen(self):
            target_scope = [
                AuthScope.CHAT_EDIT,
                AuthScope.CHAT_READ,
                AuthScope.CHANNEL_MODERATE,
            ]

            auth = UserAuthenticator(self.twitch, target_scope)
            token = os.environ["TWITCHTOKEN"]
            refresh_token = os.environ["TWITCHREFRESHTOKEN"]
            await self.twitch.set_user_authentication(
                token, target_scope, refresh_token
            )

            chat = await Chat(self.twitch)

            async def on_ready(ready_event: EventData):
                await ready_event.chat.join_room(self.channel)
                print(bc.ROOT + "ONE@TWITCH: " + ad.TEXT + "connected to Twitch")

            async def on_message(message):
                print(bc.FOLD + "ONE@TWITCH: " + ad.TEXT + message.text)
                neuron = config["twitch"].get("neuron", "alpha")
                lab.source.send(message.text, neuron, "untrusted")
                prefix = config["twitch"].get(
                    "prefix",
                    "Your name is Prism, the Architect. Please answer questions for your audience.",
                )
                bias = config["twitch"].get("bias", get_identity())
                messenger = str(get_identity())
                context = [
                    f"{propulsion}{messenger}{ship} What is the meaning of life?",
                    f"{propulsion}{bias}{ship} Forty-six and two.",
                    propulsion + (messenger) + ship + " " + message.text,
                ]
                if random.random() > 0.666:
                    return
                output = await head.gen(bias=bias, ctx=context, prefix=prefix)
                await asyncio.sleep(random.choice([7, 9]))
                print(f"{bc.CORE}ONE@TWITCH: {ad.TEXT}{output[1]}")
                lab.source.send(output[1], neuron, "trusted")
                await chat.send_message(self.channel, output[1])

            chat.register_event(ChatEvent.READY, on_ready)
            chat.register_event(ChatEvent.MESSAGE, on_message)

            chat.start()

            while True:
                await asyncio.sleep(6.66)

    # Usage example
    channel = os.environ["TWITCHCHANNEL"]
    client_id = os.environ["TWITCHCLIENT"]
    client_secret = os.environ["TWITCHSECRET"]
    oauth_token = os.environ["TWITCHTOKEN"]

    listener = TwitchBot(
        client_id, client_secret, oauth_token, username=channel, channel=channel
    )
    await listener.listen()
