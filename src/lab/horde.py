import asyncio
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import ray
import requests

from common import colors
from events import consumer, producer


def main(config):
    asyncio.run(monitor())


async def monitor():
    while True:
        try:
            await asyncio.sleep(6.66)
            item = consumer("generate_image")
            if item:
                image = await generate()
                producer(
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
            # "prompt": "((monolithic stone robot head)) with a (((large tree branch growing into his face))), head and shoulders are visible, head is looking left, BadDream###nude, naked, ((bad quality, worst quality)), (((eyes, mouth, nose, legs, arms, hands, feet, teeth)))",
            "prompt": "monolithic stone robot head with a large (wooden tree branch:1.2) growing into his face###(ugly, bad quality, worst quality, medium quality, low resolution, medium resolution, bad hands, blurry, distorted, twisted, watermark, mutant, amorphous, elongated, elastigirl, duplicate, tumor, cancer, fat, pregnant:1.3)",
            "models": [
                # "Deliberate 3.0",
                "Deliberate",
                # "DreamShaper",
                # "GhostMix",
            ],
            "source": source,
            # "mask": mask,
            "source_processing": "img2img",
            "image_is_control": False,
            "return_control_map": False,
            "height": 512,
            "width": 512,
            "sampler_name": "k_euler_a",
            "steps": 30,
            "control_type": "hed",
            "denoising_strength": 0.7,
            "cfg_scale": 8.0,
            "clip_skip": 1,
            "hires_fix": False,
            "karras": False,
            # "upscale": "x2",
            "tis": [
                # {"name": "7808", "strength": 1}, ## easynegative
                # {"name": "4629", "strength": 1}, ## ng_deepnegative_v1_75t
                # {"name": "72437", "strength": 1} ## BadDream
            ],
        }

        timeout = aiohttp.ClientTimeout(total=3600)

        print(
            f"{colors.RED}ONE@HORDE:{colors.WHITE} Requesting an image from the AI Horde. Please wait."
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
        logging.error(e)


if __name__ == "__main__":
    main()
