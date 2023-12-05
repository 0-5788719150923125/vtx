import asyncio
import base64
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import ray
import requests

from common import colors
from pipe import consumer, producer


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
            "prompt": "(masterpiece, top quality, best quality, official art, beautiful and aesthetic:1.2), (robot:1.3) with a ((tree branch:1.2)) growing through his face, (fractal art:1.3), ng_deepnegative_v1_75t, easynegative",
            # "prompt": "giant robot head with a large contraption piercing through his face, monolithic, ancient monument, ((colorful:1.2)), (((cinematic))), leviathan###blue",
            # "prompt": "robot head with a large wire piercing his face, (((masterpiece))), ((hyper-realistic)), ((top quality)), ((best quality)), ((anime)), (colorful), (official art, beautiful and aesthetic:1.2)",
            "models": [
                "Deliberate 3.0",
                "Deliberate",
                "GhostMix",
                # "DreamShaper"
            ],
            "source": source,
            # "mask": mask,
            "source_processing": "img2img",
            "height": 512,
            "width": 512,
            "sampler_name": "k_dpmpp_sde",
            "steps": 30,
            "control_type": "canny",
            "image_is_control": True,
            "return_control_map": False,
            "denoising_strength": 0.4,
            "cfg_scale": 7.0,
            "clip_skip": 2,
            "hires_fix": True,
            "karras": True,
            "upscale": "x2",
            "tis": [
                {"name": "easynegative", "strength": 1},
                {"name": "ng_deepnegative_v1_75t", "strength": 1},
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
