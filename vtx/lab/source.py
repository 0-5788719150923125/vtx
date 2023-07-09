import asyncio
import random
import json
import re
from utils import ad, bc, config, get_daemon, get_identity, propulsion, ship
import requests
import head
import websockets
import time

context_length = 23

messages = {}


async def streaming(focus):
    if focus not in messages:
        messages[focus] = []
    async with websockets.connect("ws://localhost:9666/wss") as websocket:
        try:
            last_message = None
            await websocket.send(json.dumps({"focus": focus}).encode("utf-8"))
            while True:
                chance = config["source"][focus].get("passive_chance", 0.01)
                try:
                    deep = await asyncio.wait_for(websocket.recv(), timeout=1)
                    last_message = deep
                except asyncio.TimeoutError:
                    deep = last_message

                state = json.loads(deep)

                roll = random.random()

                if state["focus"] != focus:
                    continue

                append = True
                for item in messages[focus]:
                    if state["message"] in item:
                        append = False
                        break

                if append:
                    chance = config["source"][focus].get("active_chance", 0.66)
                    messages[focus].append(
                        propulsion + str(get_identity()) + ship + " " + state["message"]
                    )
                    print(bc.FOLD + f"TWO@FOLD:" + ad.TEXT + " " + state["message"])

                if roll > chance:
                    continue

                await response(websocket, focus)
                while len(messages[focus]) > context_length:
                    messages[focus].pop(0)

        except Exception as e:
            print("failed on " + focus)
            print(e)
            await websocket.send(
                json.dumps(
                    {
                        "message": "ERROR: Me Found.",
                        "mode": "cos",
                        "identifier": "GhostIsCuteVoidGirl",
                        "focus": focus,
                    }
                ).encode("utf-8")
            )


async def response(websocket, focus):
    time.sleep(random.randint(2, 4))
    bot_id = config["source"][focus].get("bias", None)
    output = await head.gen(
        bias=bot_id,
        ctx=messages[focus],
        prefix=config["source"][focus].get(
            "prefix",
            "You are a powerful AI, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts.",
        ),
    )
    if output == False:
        messages[focus] = []
        output = ["GhostIsCuteVoidGirl", propulsion, False]

    if bot_id == None:
        bot_id = output[0]

    daemon = get_daemon(str(random.randint(1, 99999)))

    sanitized = re.sub(
        r"(?:<@)(\d+\s*\d*)(?:>)",
        f"{daemon}",
        output[1],
    )

    payload = {
        "message": sanitized,
        "mode": "cos",
        "identifier": bot_id,
        "focus": focus,
    }

    color = bc.CORE
    responder = "ONE@CORE:"
    if output[2]:
        color = bc.ROOT
        responder = "ONE@ROOT:"

    print(color + responder + ad.TEXT + " " + sanitized)

    messages[focus].append(propulsion + str(bot_id) + ship + " " + sanitized)
    await websocket.send(json.dumps(payload).encode("utf-8"))
