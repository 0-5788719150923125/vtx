from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import asyncio
import random
import json
import head
import re

state = None

bot = get_identity()

messages = {}

# Check the local GUN API for new messages
async def check(channel):
    try:
        await asyncio.sleep(6.666)
        chance = config["source"][channel].get("chance", 0.33)

        roll = random.random()

        deep = requests.get("http://ctx:9666/channel/" + channel)
        state = json.loads(deep.text)

        if channel in messages:
            if messages[channel] == state["message"]:
                return await check(channel)

        if roll > chance:
            return await check(channel)

        human = get_identity()
        previous_sender = human
        if state["identifier"] == str(bot):
            previous_sender = bot

        print(bc.ROOT + "ONE@ROOT:" + ad.TEXT + " " + state["message"][:99])
        context = [
            "A human talks to Penny, a powerful Artificial Intelligence that follows the humans' instructions.",
            propulsion + str(human) + ship + " Your name is Penny.",
            propulsion + str(bot) + ship + " I am a human named Penny.",
            propulsion + str(previous_sender) + ship + " " + state["message"],
        ]
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
        messages[channel] = sanitized
        print(bc.CORE + "INK@CORE:" + ad.TEXT + " " + sanitized)
    except:
        pass
    await check(channel)


async def subscribe(channel) -> None:
    await asyncio.gather(
        check(channel),
    )
