import asyncio
import threading
import random
import time
import json
import re
import websocket
import websockets
from pprint import pprint
from cerberus import Validator
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


def orchestrate(config):
    result = validation(config["source"])
    if not result:
        return

    tasks = {}
    while True:
        for focus in config["source"]["focus"]:
            for task in tasks.copy():
                if not tasks[task].is_alive():
                    del tasks[task]

            if "l" + focus not in tasks:
                t = threading.Thread(
                    target=asyncio.run,
                    args=(listener(config, focus),),
                    daemon=True,
                    name="l" + focus,
                )
                tasks[t.name] = t
                t.start()
            if "r" + focus not in tasks:
                t = threading.Thread(
                    target=asyncio.run,
                    args=(responder(config, focus),),
                    daemon=True,
                    name="r" + focus,
                )
                tasks[t.name] = t
                t.start()

        time.sleep(6.66)


def validation(config):
    schema = {
        "focus": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "passive_chance": {"type": "float"},
                    "active_chance": {"type": "float"},
                    "personas": {"type": "list"},
                },
            },
        },
        "info": {"type": "string"},
        "model": {"type": "string"},
        "to_gpu": {"type": "boolean"},
        "to_fp16": {"type": "boolean"},
        "max_new_tokens": {"type": "integer"},
        "training": {"type": "dict"},
        "gpu_index": {"type": "integer"},
        "low_memory": {"type": "boolean"},
        "petals": {"type": "boolean"},
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


async def listener(config, focus):
    if focus not in messages:
        messages[focus] = []
        chance[focus] = config["source"]["focus"][focus].get("passive_chance", 0.01)
        mine[focus] = False
    async with websockets.connect("ws://localhost:9666/ws") as websocket:
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
                    chance[focus] = config["source"]["focus"][focus].get(
                        "active_chance", 0.66
                    )
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
    personas = config["source"]["focus"][focus].get("personas", None)
    persona = "You are a powerful AI, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts."
    bias = None
    identity = None
    if personas:
        filtered = [
            config["personas"][key] for key in personas if key in config["personas"]
        ]
        identity = random.choice(filtered)
        bias = identity.get("bias")
        persona = propulsion + str(bias) + ship + " " + identity.get("persona")

    output = await head.ctx.gen(
        bias=bias,
        ctx=messages[focus],
        prefix=persona,
    )

    if output[0] == False:
        print(output[1])
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
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

    if sanitized == "" or sanitized.startswith(" "):
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
        return

    color = bc.CORE
    responder = "ONE@CORE:"
    if output[2]:
        color = bc.ROOT
        responder = "ONE@ROOT:"

    print(color + responder + ad.TEXT + " " + sanitized)

    messages[focus].append(propulsion + str(bias) + ship + " " + sanitized)
    mine[focus] = True
    chance[focus] = config["source"]["focus"][focus].get("passive_chance", 0.01)
    send(sanitized, focus, "cos", bias)


def send(message, focus, mode, identifier=get_identity()):
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:9666/ws")
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
