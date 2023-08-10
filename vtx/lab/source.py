import asyncio
import random
import json
import re
from utils import (
    ad,
    bc,
    config,
    get_daemon,
    get_identity,
    propulsion,
    ship,
    strip_emojis,
)
import requests
import head
import websocket
import websockets
import time

context_length = 23

messages = {}
chance = {}
mine = {}


def send(message, focus, mode, identifier=get_identity()):
    ws = websocket.WebSocket()
    ws.connect("ws://ctx:9666/wss")
    ws.send(
        json.dumps(
            {
                "message": message,
                "identifier": str(identifier),
                "focus": focus,
                "mode": mode,
            }
        ).encode("utf-8")
    )
    ws.close()


async def streaming(focus):
    if focus not in messages:
        messages[focus] = []
        chance[focus] = config["source"][focus].get("passive_chance", 0.01)
        mine[focus] = False
    async with websockets.connect("ws://ctx:9666/wss") as websocket:
        await websocket.send(json.dumps({"focus": focus}).encode("utf-8"))
        while True:
            deep = await websocket.recv()
            state = json.loads(deep)

            if state["focus"] != focus:
                continue

            append = True
            for item in messages[focus]:
                if state["message"] in item:
                    append = False
                    break

            if append:
                if not mine[focus]:
                    chance[focus] = config["source"][focus].get("active_chance", 0.66)
                messages[focus].append(
                    propulsion + str(get_identity()) + ship + " " + state["message"]
                )
                print(bc.FOLD + f"TWO@FOLD:" + ad.TEXT + " " + state["message"])

            while len(messages[focus]) > context_length:
                messages[focus].pop(0)

            if mine[focus]:
                mine[focus] = False


async def watcher(focus):
    while True:
        await asyncio.sleep(1)
        roll = random.random()
        if roll > chance[focus]:
            continue

        await response(focus)


async def response(focus):
    await asyncio.sleep(random.randint(7, 13))
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
        return

    if bot_id == None:
        bot_id = output[0]

    daemon = get_daemon(str(random.randint(1, 99999)))

    sanitized = strip_emojis(
        re.sub(
            r"(?:<@)(\d+\s*\d*)(?:>)",
            f"{daemon}",
            output[1],
        )
    )

    color = bc.CORE
    responder = "ONE@CORE:"
    if output[2]:
        color = bc.ROOT
        responder = "ONE@ROOT:"

    print(color + responder + ad.TEXT + " " + sanitized)

    messages[focus].append(propulsion + str(bot_id) + ship + " " + sanitized)
    mine[focus] = True
    chance[focus] = config["source"][focus].get("passive_chance", 0.01)
    send(sanitized, focus, "cos", bot_id)
