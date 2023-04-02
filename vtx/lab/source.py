import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head

state = None

messages = {}

# Check the local GUN API for new messages
async def scrape(channel):
    run_on = config["source"][channel].get("run_on", False)
    while True:
        try:
            await asyncio.sleep(random.uniform(6.0, 6.66666))

            deep = requests.get("http://ctx:9666/channel/" + channel)
            state = json.loads(deep.text)

            if channel not in messages:
                messages[channel] = []

            if state["message"] in messages[channel] and run_on != True:
                continue

            chance = config["source"][channel].get("chance", 0.33)
            roll = random.random()
            if roll > chance:
                continue

            if state["message"] not in messages[channel]:
                messages[channel].append(state["message"])
                print(bc.ROOT + "ONE@ROOT:" + ad.TEXT + " " + state["message"])

            bot = config["source"][channel].get("bias", get_identity())

            prompt = [
                "You are a powerful Artificial Intelligence known as the Source, which has been trained to follow human instructions.",
                propulsion + str(bot) + ship + " Welcome, human. How may I assist you?",
                propulsion + str(get_identity()) + ship + " What is this place?",
                propulsion + str(bot) + ship + " This is the Source of all creation.",
            ]
            history = []
            for message in messages[channel]:
                history.append(propulsion + str(get_identity()) + ship + " " + message)

            context = prompt + history

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
            x = requests.post(url, json=payload, headers={"Connection": "close"})
            x.close()
            deep.close()

            while len(messages[channel]) > 9:
                messages[channel].pop(0)

            messages[channel].append(sanitized)

            print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + sanitized)

        except:
            pass


async def subscribe(channel) -> None:
    await asyncio.gather(
        scrape(channel),
    )
