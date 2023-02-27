from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import asyncio
import random
import json
import head
import re

state = None

messages = {}

# Check the local GUN API for new messages
async def check(channel):
    try:
        await asyncio.sleep(random.uniform(6.0, 6.66666))

        deep = requests.get("http://ctx:9666/channel/" + channel)
        state = json.loads(deep.text)

        if channel not in messages:
            messages[channel] = []

        if state["message"] in messages[channel]:
            return await check(channel)

        chance = config["source"][channel].get("chance", 0.33)
        roll = random.random()
        if roll > chance:
            return await check(channel)

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
        daemon = get_daemon(random.randint(1, 9999))["name"]
        sanitized = re.sub(
            r"(?:<@)(\d+\s*\d*)(?:>)",
            f"{daemon}",
            generation[1],
        )
        myobj = {"message": sanitized, "identifier": str(bot)}
        x = requests.post(url, json=myobj, headers={"Connection": "close"})
        x.close()
        deep.close()

        if len(messages[channel]) > 3:
            messages[channel].pop(0)

        messages[channel].append(sanitized)

        print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + sanitized)

    except Exception as e:
        print(e)
    await check(channel)


async def subscribe(channel) -> None:
    await asyncio.gather(
        check(channel),
    )
