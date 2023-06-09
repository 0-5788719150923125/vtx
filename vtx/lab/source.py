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
def send(message, focus, mode: str = "cos", identifier: str = str(get_identity())):
    url = "http://ctx:9666/send/" + focus
    payload = {"message": message, "identifier": identifier, "mode": mode}
    x = requests.post(url, json=payload)


# Check the local GUN API for new messages
async def polling(focus):
    run_on = config["source"][focus].get("run_on", False)
    while True:
        try:
            await asyncio.sleep(random.uniform(8.0, 8.8888888))

            deep = requests.get("http://ctx:9666/receive/" + focus, timeout=6)
            state = json.loads(deep.text)

            if focus not in messages:
                messages[focus] = []

            skip = False
            for item in messages[focus]:
                if state["message"] in item and run_on != True:
                    skip = True
                    break

            if skip:
                continue

            chance = config["source"][focus].get("chance", 0.33)
            roll = random.random()
            if roll > chance:
                continue

            append = True
            for item in messages[focus]:
                if state["message"] in item:
                    append = False
                    break

            if append:
                messages[focus].append(
                    propulsion + str(get_identity()) + ship + " " + state["message"]
                )
                print(bc.FOLD + f"TWO@FOLD:" + ad.TEXT + " " + state["message"])

            bot_id = config["source"][focus].get("bias", None)

            generation = await head.gen(
                bias=bot_id,
                ctx=messages[focus],
                prefix=config["source"][focus].get(
                    "prefix",
                    "You are a powerful AI, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts.",
                ),
            )

            if bot_id == None:
                bot_id = generation[0]

            if generation[0] == "error":
                messages[focus] = []
                continue

            daemon = get_daemon(random.randint(1, 9999))["name"]
            sanitized = re.sub(
                r"(?:<@)(\d+\s*\d*)(?:>)",
                f"{daemon}",
                generation[1],
            )

            send(sanitized, focus, "cos", str(bot_id))

            while len(messages[focus]) > context_length:
                messages[focus].pop(0)

            messages[focus].append(propulsion + str(bot_id) + ship + " " + sanitized)

            color = bc.CORE
            responder = "ONE@CORE:"
            if generation[2]:
                color = bc.ROOT
                responder = "ONE@ROOT:"

            print(color + responder + ad.TEXT + " " + sanitized)

        except Exception as e:
            print(focus + " failed to connect")
            print(e)


async def subscribe(channel) -> None:
    await asyncio.gather(
        polling(channel),
    )
