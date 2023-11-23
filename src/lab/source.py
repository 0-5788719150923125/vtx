import asyncio
import json
import logging
import random
import re
import threading
import time
from pprint import pprint

import websocket
import websockets
from cerberus import Validator

import head
from common import colors, get_identity, remove_invisible_characters, strip_emojis

context_length = 23

messages = {}
frequency = {}
mine = {}


def main(config):
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


if __name__ == "main":
    main(config)


def validation(config):
    schema = {
        "focus": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "passive_frequency": {"type": "float"},
                    "active_frequency": {"type": "float"},
                    "personas": {"type": "list"},
                },
            },
        },
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


async def listener(config, focus):
    if focus not in messages:
        messages[focus] = []
        frequency[focus] = config["source"]["focus"][focus].get(
            "passive_frequency", 0.01
        )
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
                if state["message"] in item["message"]:
                    append = False
                    break

            if append:
                if not mine[focus]:
                    frequency[focus] = config["source"]["focus"][focus].get(
                        "active_frequency", 0.66
                    )
                messages[focus].append(
                    {"bias": int(get_identity()), "message": state["message"]}
                )
                print(
                    colors.BLUE + f"ONE@FOLD:" + colors.WHITE + " " + state["message"]
                )

            while len(messages[focus]) > context_length:
                messages[focus].pop(0)

            if mine[focus]:
                mine[focus] = False


async def responder(config, focus):
    while True:
        await asyncio.sleep(1)
        roll = random.random()
        if roll > frequency[focus]:
            continue

        await response(config, focus)


async def response(config, focus):
    await asyncio.sleep(random.randint(7, 13))
    personas = config["source"]["focus"][focus].get("personas", None)

    success, bias, output, seeded = await head.ctx.chat(
        ctx=messages[focus],
        personas=personas,
        max_new_tokens=222,
        eos_tokens=["\n", "\n\n", "\\"],
    )

    if success == False:
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
        return

    sanitized = remove_invisible_characters(strip_emojis(output))

    while sanitized.startswith(" "):
        sanitized = sanitized[1:]

    if sanitized == "" or {"bias": int(bias), "message": sanitized} in messages[focus]:
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
        return

    color = colors.RED
    responder = "ONE@CORE:"
    if seeded:
        color = colors.GREEN
        responder = "ONE@ROOT:"

    print(color + responder + colors.WHITE + " " + sanitized)

    messages[focus].append({"bias": int(bias), "message": sanitized})

    mine[focus] = True
    frequency[focus] = config["source"]["focus"][focus].get("passive_frequency", 0.01)
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
