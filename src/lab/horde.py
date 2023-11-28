import asyncio
import base64
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
        await asyncio.sleep(6.66)
        item = await queue.get()
        if item is None:
            break
        await asyncio.gather(respond(item))


async def respond(data):
    image = await generate()
    post_event("receive_image", data=data, image=image)


async def generate():
    api = "http://localhost:5000/generate"

    source = None
    mask = None

    try:
        if os.path.exists("/data/source.jpg"):
            with open("/data/source.jpg", "rb") as file:
                source = base64.b64encode(file.read()).decode("utf-8")

        if os.path.exists("/data/mask.jpg"):
            with open("/data/mask.jpg", "rb") as file:
                mask = base64.b64encode(file.read()).decode("utf-8")

        data = {
            "prompt": "robot head with a large electrical wire protruding from his face, (((masterpiece))), ((hyper-realistic)), ((top quality)), ((best quality)), ((anime)), (colorful), (official art, beautiful and aesthetic:1.2)",
            # "prompt": "robot head with a large wire piercing his face",
            "models": ["GhostMix"],
            "source": source,
            "mask": mask,
            "height": 1024,
            "width": 1024,
            "sampler_name": "k_euler",
            "steps": 50,
            "control_type": "hed",
            "image_is_control": True,
            "denoising_strength": 0.85,
            "cfg_scale": 7.5,
            "clip_skip": 1,
            "hires_fix": True,
            "karras": False,
        }

        timeout = aiohttp.ClientTimeout(total=3600)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api, json=data) as response:
                response_data = await response.json()
                if response.status != 200:
                    logging.error(
                        f"GET request failed with status code: {response.status}"
                    )
                    logging.error(response_data["err"])
                    return

                response_data = await response.json()

                return response_data["data"]

    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
