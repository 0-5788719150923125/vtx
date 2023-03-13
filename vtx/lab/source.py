import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head
import logging

logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.ERROR,
)

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

            messages[channel].append(state["message"])

            bot = get_identity()

            print(bc.ROOT + "ONE@ROOT:" + ad.TEXT + " " + state["message"][:99])

            prompt = [
                "A human talks to Penny, a powerful Artificial Intelligence that follows the humans' instructions.",
                propulsion + str(get_identity()) + ship + " Your name is Penny.",
                propulsion + str(bot) + ship + " I am a human named Penny.",
            ]
            history = []
            for message in messages[channel]:
                history.append(propulsion + str(get_identity()) + ship + " " + message)

            context = prompt + history

            url = "http://ctx:9666/message/" + channel
            generation = await head.gen(int(bot), context)

            if generation[0] == "[ERROR]":
                messages[channel] = []
                raise

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

            def truncate_history(history):
                if len(history) > 3:
                    history.pop(0)
                    truncate_history(history)

            truncate_history(messages[channel])

            messages[channel].append(sanitized)

            print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + sanitized)

        except Exception as e:
            print(e)
            payload = {
                "message": "ERROR: Me Found.",
                "identifier": "GhostIsCuteVoidGirl",
            }
            x = requests.post(url, json=payload, headers={"Connection": "close"})
            x.close()


async def subscribe(channel) -> None:
    await asyncio.gather(
        scrape(channel),
    )
