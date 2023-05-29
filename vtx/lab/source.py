import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head

context_length = 23

messages = {}


# Check the local GUN API for new messages
async def polling(channel):
    run_on = config["source"][channel].get("run_on", False)
    while True:
        try:
            await asyncio.sleep(random.uniform(8.0, 8.8888888))

            deep = requests.get("http://ctx:9666/channel/" + channel)
            state = json.loads(deep.text)

            if channel not in messages:
                messages[channel] = []

            skip = False
            for item in messages[channel]:
                if state["message"] in item and run_on != True:
                    skip = True
                    break

            if skip:
                continue

            chance = config["source"][channel].get("chance", 0.33)
            roll = random.random()
            if roll > chance:
                continue

            append = True
            for item in messages[channel]:
                if state["message"] in item:
                    append = False
                    break

            if append:
                messages[channel].append(
                    propulsion + str(get_identity()) + ship + " " + state["message"]
                )
                print(bc.FOLD + "PEN@ROOT:" + ad.TEXT + " " + state["message"])

            bot_id = config["source"][channel].get("bias", get_identity())

            prompt = [
                propulsion + str(bot_id) + ship + " Welcome, human.",
                propulsion + str(get_identity()) + ship + " Where am I?",
                propulsion
                + str(bot_id)
                + ship
                + f" You are in the Source of All Areation. How may we assist you today?",
            ]

            context = prompt + messages[channel]

            url = "http://ctx:9666/message/" + channel
            generation = await head.gen(
                int(bot_id),
                context,
                prefix=config["source"][channel].get(
                    "prefix",
                    "You are a powerful Artificial Intelligence computer, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts.",
                ),
            )

            if generation[0] == "error":
                messages[channel] = []

            daemon = get_daemon(random.randint(1, 9999))["name"]
            sanitized = re.sub(
                r"(?:<@)(\d+\s*\d*)(?:>)",
                f"{daemon}",
                generation[1],
            )
            payload = {"message": sanitized, "identifier": str(bot_id)}
            x = requests.post(url, json=payload)

            while len(messages[channel]) > context_length:
                messages[channel].pop(0)

            messages[channel].append(propulsion + str(bot_id) + ship + " " + sanitized)

            color = bc.CORE
            responder = "INK@CORE:"
            if generation[2]:
                color = bc.ROOT
                responder = "ONE@ROOT:"

            print(color + responder + ad.TEXT + " " + sanitized)

        except Exception as e:
            print(e)


async def subscribe(channel) -> None:
    await asyncio.gather(
        polling(channel),
    )
