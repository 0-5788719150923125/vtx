import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import requests

from events import post_event, subscribe_event


def main(config):
    asyncio.run(monitor())


async def monitor():
    queue = asyncio.Queue()

    def build_queue(data):
        queue.put_nowait(data)

    subscribe_event("generate_image", build_queue)

    processing_task = asyncio.create_task(process_queue(queue))

    try:
        while True:
            await asyncio.sleep(6.66)

    finally:
        await queue.put(None)
        await processing_task


async def process_queue(queue):
    while True:
        print("processing generation request")
        await asyncio.sleep(6.66)
        item = await queue.get()
        if item is None:
            break
        await asyncio.gather(respond(item))


async def respond(data):
    print(data)
    image = await generate()
    post_event("receive_image", data=data, image=image)


async def generate():
    api = "http://localhost:5000/generate"

    data = {
        "prompt": "((anime)), ((in the style of dragon ball z)), epic (((1robot:1.2))) (head:1.3) is connected to a large (wire:1.3), wire is piercing the ((face:1.2)), (((masterpiece))), ((top quality)), ((best quality)), (official art, colorful, anime, beautiful and aesthetic:1.2), (fractal art:1.3)",
        "models": ["GhostMix"],
        "height": 1024,
        "width": 1024,
        "sampler_name": "k_lms",
        "steps": 50,
        "control_type": "canny",
        "image_is_control": True,
        "denoising_strength": 0.65,
        "cfg_scale": 7.5,
        "clip_skip": 2,
        "hires_fix": True,
        "karras": True,
    }

    timeout = aiohttp.ClientTimeout(total=3600)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(api, json=data) as response:
            if response.status // 100 != 2:
                logging.error(f"GET request failed with status code: {response.status}")
                logging.error(response.text())
                return

            response_data = await response.json()

            return response_data["data"]


if __name__ == "__main__":
    main()
