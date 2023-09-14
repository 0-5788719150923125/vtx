from twitchAPI import Twitch
from twitchAPI.twitch import Twitch
from twitchAPI.pubsub import PubSub
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope, ChatEvent
from twitchAPI.chat import Chat, EventData
import asyncio
import os
import logging
from utils import ad, bc, get_identity, propulsion, ship
import head
import lab.source
import random


def main(config):
    asyncio.run(client(config))


if __name__ == "main":
    main(config)


async def client(config):
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
            self.active = False

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

            async def on_message(message):
                if self.active == True:
                    return

                self.active = True

                try:
                    print(bc.FOLD + "ONE@TWITCH: " + ad.TEXT + message.text)
                    focus = config["twitch"].get("focus", "alpha")
                    persona = config["personas"].get(config["twitch"].get("persona"))
                    lab.source.send(message.text, focus, "sin")
                    prefix = persona.get(
                        "prefix",
                        "My name is Ryan, Ink, or the Architect. I will answer questions for my audience.",
                    )
                    bias = str(persona.get("bias", get_identity()))
                    messenger = str(get_identity())
                    head.ctx.build_context(
                        propulsion + messenger + ship + " " + message.text
                    )
                    output = await head.ctx.chat(
                        bias=bias, prefix=prefix, max_new_tokens=44
                    )
                    if output[0] == False:
                        return
                    head.ctx.build_context(propulsion + bias + ship + " " + output[1])
                    await asyncio.sleep(random.choice([7, 8, 9]))
                    print(f"{bc.CORE}ONE@TWITCH: {ad.TEXT}{output[1]}")
                    await chat.send_message(self.channel, output[1])
                except Exception as e:
                    logging.error(e)

                self.active = False

            chat.register_event(ChatEvent.READY, on_ready)
            chat.register_event(ChatEvent.MESSAGE, on_message)

            chat.start()

            while True:
                await asyncio.sleep(6.66)

    # Usage example
    channel = config["twitch"].get("channel", "missiontv")
    client_id = os.environ["TWITCHCLIENT"]
    client_secret = os.environ["TWITCHSECRET"]
    oauth_token = os.environ["TWITCHTOKEN"]

    listener = TwitchBot(
        client_id, client_secret, oauth_token, username=channel, channel=channel
    )
    await listener.listen()
