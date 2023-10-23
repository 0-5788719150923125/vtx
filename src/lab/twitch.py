import asyncio
import logging
import os
import random

from twitchAPI.chat import Chat, EventData
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.pubsub import PubSub
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent

import head
import lab.source
from common import ad, bc, get_identity


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
                viewer = str(get_identity(message.user.name))
                head.ctx.build_context(bias=int(viewer), message=message.text)

                if self.active == True:
                    return

                self.active = True

                try:
                    print(bc.FOLD + "ONE@TWITCH: " + ad.TEXT + message.text)
                    focus = config["twitch"].get("focus", "alpha")
                    personas = config["twitch"].get("personas")
                    name = random.choice(personas)

                    lab.source.send(message.text, focus, "sin")

                    success, bias, output, seeded = await head.ctx.chat(
                        personas=personas, max_new_tokens=222
                    )
                    if success == False:
                        return
                    head.ctx.build_context(bias=int(bias), message=output)
                    await asyncio.sleep(random.choice([7, 8, 9]))
                    print(f"{bc.CORE}ONE@TWITCH: {ad.TEXT}{output}")
                    await chat.send_message(self.channel, f"[{name.upper()}] " + output)
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
