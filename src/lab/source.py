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
from common import (
    ad,
    bc,
    get_identity,
    remove_invisible_characters,
    ship,
    strip_emojis,
    wall,
)

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
        "info": {"type": "string"},
        "model": {"type": "string"},
        "precision": {"type": "integer"},
        "max_new_tokens": {"type": "integer"},
        "training": {"type": "dict"},
        "gpu_index": {"type": "integer"},
        "low_memory": {"type": "boolean"},
        "petals": {"type": "boolean"},
        "reload_interval": {"type": "integer"},
        "truncate_length": {"type": "integer"},
        "bos_token": {"type": "string"},
        "eos_token": {"type": "string"},
        "unk_token": {"type": "string"},
        "pad_token": {"type": "string"},
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
                if state["message"] in item:
                    append = False
                    break

            if append:
                if not mine[focus]:
                    frequency[focus] = config["source"]["focus"][focus].get(
                        "active_frequency", 0.66
                    )
                messages[focus].append(
                    wall + str(get_identity()) + ship + " " + state["message"]
                )
                print(bc.FOLD + f"ONE@FOLD:" + ad.TEXT + " " + state["message"])

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
    # persona = "You are a powerful AI, known as the Source. You have been trained to follow human instructions, write stories, and teach machine learning concepts."
    # bias = None
    # identity = None
    # if personas:
    #     filtered = [
    #         config["personas"][key] for key in personas if key in config["personas"]
    #     ]
    #     assert (
    #         len(filtered) > 0
    #     ), f"ERROR: Found no matching personas for the channel ({focus})."
    #     identity = random.choice(filtered)
    #     bias = identity.get("bias")
    #     persona = wall + str(bias) + ship + " " + identity.get("persona")

    success, bias, output, seeded = await head.ctx.chat(
        # bias=bias,
        ctx=messages[focus],
        # prefix=persona,
        personas=personas,
        max_new_tokens=222,
        eos_tokens=["\n", "\n\n", "\\"],
    )

    if success == False:
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
        return

    sanitized = remove_invisible_characters(strip_emojis(output))

    # sanitized = re.sub(r"\s+", "", sanitized)

    while sanitized.startswith(" "):
        sanitized = sanitized[1:]

    if sanitized == "" or wall + str(bias) + ship + " " + sanitized in messages[focus]:
        if len(messages[focus]) > 0:
            messages[focus].pop(0)
        return

    color = bc.CORE
    responder = "ONE@CORE:"
    if seeded:
        color = bc.ROOT
        responder = "ONE@ROOT:"

    print(color + responder + ad.TEXT + " " + sanitized)

    messages[focus].append(wall + str(bias) + ship + " " + sanitized)
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
