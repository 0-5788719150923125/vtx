import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head

context_length = 23

messages = {}


# Send a message to the Source
def send(message, neuron):
    url = "http://ctx:9666/send/" + neuron
    payload = {"message": message, "identifier": str(get_identity())}
    x = requests.post(url, json=payload)


# Check the local GUN API for new messages
async def polling(neuron):
    run_on = config["source"][neuron].get("run_on", False)
    while True:
        try:
            await asyncio.sleep(random.uniform(8.0, 8.8888888))

            deep = requests.get("http://ctx:9666/receive/" + neuron, timeout=5)
            state = json.loads(deep.text)

            if neuron not in messages:
                messages[neuron] = []

            skip = False
            for item in messages[neuron]:
                if state["message"] in item and run_on != True:
                    skip = True
                    break

            if skip:
                continue

            chance = config["source"][neuron].get("chance", 0.33)
            roll = random.random()
            if roll > chance:
                continue

            append = True
            for item in messages[neuron]:
                if state["message"] in item:
                    append = False
                    break

            if append:
                messages[neuron].append(
                    propulsion + str(get_identity()) + ship + " " + state["message"]
                )
                tag = random.choice(["ONE", "TWO"])
                print(bc.FOLD + f"{tag}@FOLD:" + ad.TEXT + " " + state["message"])

            bot_id = config["source"][neuron].get("bias", get_identity())

            prompt = [
                propulsion + str(bot_id) + ship + " Welcome, human.",
                propulsion + str(get_identity()) + ship + " Where am I?",
                propulsion
                + str(bot_id)
                + ship
                + f" You are are speaking to the source of all creation. Make it quick.",
            ]

            context = prompt + messages[neuron]

            generation = await head.gen(
                int(bot_id),
                context,
                prefix=config["source"][neuron].get(
                    "prefix",
                    "You are a powerful Artificial Intelligence computer, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts.",
                ),
            )

            if generation[0] == "error":
                messages[neuron] = []

            daemon = get_daemon(random.randint(1, 9999))["name"]
            sanitized = re.sub(
                r"(?:<@)(\d+\s*\d*)(?:>)",
                f"{daemon}",
                generation[1],
            )
            url = "http://ctx:9666/send/" + neuron
            payload = {"message": sanitized, "identifier": str(bot_id)}
            x = requests.post(url, json=payload)

            while len(messages[neuron]) > context_length:
                messages[neuron].pop(0)

            messages[neuron].append(propulsion + str(bot_id) + ship + " " + sanitized)

            color = bc.CORE
            responder = "ONE@CORE:"
            if generation[2]:
                color = bc.ROOT
                responder = "ONE@ROOT:"

            print(color + responder + ad.TEXT + " " + sanitized)

        except:
            pass


async def subscribe(channel) -> None:
    await asyncio.gather(
        polling(channel),
    )
