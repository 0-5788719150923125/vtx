import asyncio
import random
import json
import re
import websocket
import websockets
from pprint import pprint
from utils import (
    ad,
    bc,
    get_daemon,
    get_identity,
    propulsion,
    ship,
    strip_emojis,
)
import head

context_length = 23

messages = {}
chance = {}
mine = {}


async def orchestrate(config):
    tasks = {}
    while True:
        for focus in config:
            for task in tasks.copy():
                if tasks[task].done() or tasks[task].cancelled():
                    del tasks[task]

            if "l" + focus not in tasks:
                l = asyncio.create_task(listener(config, focus))
                l.set_name("l" + focus)
                tasks[l.get_name()] = l
            if "r" + focus not in tasks:
                r = asyncio.create_task(responder(config, focus))
                r.set_name("r" + focus)
                tasks[r.get_name()] = r

        await asyncio.sleep(6.66)


async def listener(config, focus):
    if focus not in messages:
        messages[focus] = []
        chance[focus] = config[focus].get("passive_chance", 0.01)
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
                    chance[focus] = config[focus].get("active_chance", 0.66)
                messages[focus].append(
                    propulsion + str(get_identity()) + ship + " " + state["message"]
                )
                print(bc.FOLD + f"TWO@FOLD:" + ad.TEXT + " " + state["message"])

            while len(messages[focus]) > context_length:
                messages[focus].pop(0)

            if mine[focus]:
                mine[focus] = False


async def responder(config, focus):
    while True:
        await asyncio.sleep(1)
        roll = random.random()
        if roll > chance[focus]:
            continue

        await response(config, focus)


async def response(config, focus):
    await asyncio.sleep(random.randint(7, 13))
    identities = config[focus].get("identities", None)
    persona = config[focus].get(
        "prefix",
        "You are a powerful AI, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts.",
    )
    bias = None
    identity = None
    if identities:
        identity = random.choice(identities)
        bias = identity.get("bias")
        persona = identity.get("persona")

    output = await head.gen(
        bias=bias,
        ctx=messages[focus],
        prefix=persona,
    )
    if output == False:
        messages[focus] = []
        return

    if bias == None:
        bias = output[0]

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

    messages[focus].append(propulsion + str(bias) + ship + " " + sanitized)
    mine[focus] = True
    chance[focus] = config[focus].get("passive_chance", 0.01)
    send(sanitized, focus, "cos", bias)


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
