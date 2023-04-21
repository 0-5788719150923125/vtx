import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head

messages = {}

# Check the local GUN API for new messages
async def polling(channel):
    run_on = config["source"][channel].get("run_on", False)
    while True:
        try:
            await asyncio.sleep(random.uniform(6.0, 6.66666))

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
                print(bc.ROOT + "ONE@ROOT:" + ad.TEXT + " " + state["message"])

            bot = config["source"][channel].get("bias", get_identity())

            prompt = [
                "You are a powerful Artificial Intelligence computer, known as the Source. You have been trained to follow human instructions.",
                propulsion + str(bot) + ship + " Welcome, human. How may I assist you?",
                propulsion + str(get_identity()) + ship + " Where am I?",
                propulsion
                + str(bot)
                + ship
                + " You have found the Source of all creation.",
            ]

            context = prompt + messages[channel]

            url = "http://ctx:9666/message/" + channel
            generation = await head.gen(int(bot), context)

            if generation[0] == "error":
                messages[channel] = []
                generation[1] = "ERROR: Me Found."

            daemon = get_daemon(random.randint(1, 9999))["name"]
            sanitized = re.sub(
                r"(?:<@)(\d+\s*\d*)(?:>)",
                f"{daemon}",
                generation[1],
            )
            payload = {"message": sanitized, "identifier": str(bot)}
            x = requests.post(url, json=payload)

            while len(messages[channel]) > 9:
                messages[channel].pop(0)

            messages[channel].append(propulsion + str(bot) + ship + " " + sanitized)

            print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + sanitized)

        except:
            pass


async def subscribe(channel) -> None:
    await asyncio.gather(
        polling(channel),
    )
