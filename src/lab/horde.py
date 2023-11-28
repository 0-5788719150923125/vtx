import asyncio
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import ray
import requests

from common import colors
from events import post_event, subscribe_event
from pipe import consumer, producer, queue


def main(config):
    asyncio.run(monitor())


async def monitor():
    while True:
        try:
            await asyncio.sleep(6.66)
            ref = consumer.remote(queue, "generate_image")
            item = ray.get(ref)

            if item:
                image = await generate()
                producer.remote(
                    queue,
                    {
                        **item,
                        "event": "publish_image",
                        "response": "my response",
                        "image": image,
                    },
                )
        except Exception as e:
            logging.error(e)


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
            "prompt": "(((cinematic))) giant robot head with a large contraption piercing through his face, monolithic, ancient monument, ((colorful:1.2)), leviathan",
            # "prompt": "robot head with a large wire piercing his face, (((masterpiece))), ((hyper-realistic)), ((top quality)), ((best quality)), ((anime)), (colorful), (official art, beautiful and aesthetic:1.2)",
            "models": [
                "Deliberate 3.0",
                # "Deliberate",
                # "GhostMix"
            ],
            "source": source,
            # "mask": mask,
            "source_processing": "img2img",
            "height": 1024,
            "width": 1024,
            "sampler_name": "k_dpm_2",
            "steps": 50,
            "control_type": "hed",
            "image_is_control": False,
            "return_control_map": False,
            "denoising_strength": 0.7,
            "cfg_scale": 7.5,
            "clip_skip": 1,
            "hires_fix": True,
            "karras": True,
            # "tis": [
            #     {"name": "4629", "strength": 1},
            #     {"name": "7808", "strength": 1},
            #     {"name": "grey", "strength": 1},
            #     {"name": "brown", "strength": 1},
            #     {"name": "color grey", "strength": 1},
            #     {"name": "color brown", "strength": 1},
            # ],
        }

        timeout = aiohttp.ClientTimeout(total=3600)

        print(
            f"{colors.RED}ONE@HORDE: {colors.WHITE} Requesting an image from the AI Horde. Please wait."
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api, json=data) as response:
                response_data = await response.json()
                if response.status != 200:
                    logging.error(
                        f"GET request failed with status code: {response.status}"
                    )
                    logging.error(response_data["err"])
                    return response_data["err"]

                return response_data["data"]

    except Exception as e:
        logger.error(e)


if __name__ == "__main__":
    main()
