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
    asyncio.run(gather(config))


async def gather(config):
    await asyncio.gather(
        monitor("generate_image", "publish_image", generate, config),
        monitor("caption_image", "publish_caption", caption, config),
    )


async def monitor(subscribe_event, publish_event, func, config):
    while True:
        try:
            await asyncio.sleep(6.66)
            item = consumer(subscribe_event)
            if item:
                response = await func(config["horde"], **item)
                producer(
                    {
                        **item,
                        "event": publish_event,
                        "response": response,
                    },
                )
        except Exception as e:
            logging.error(e)


async def caption(config, *args, **kwargs):
    api = "http://127.0.0.1:5000/caption"

    try:
        data = {"source": kwargs["image"]}

        timeout = aiohttp.ClientTimeout(total=3600)

        print(
            f"{colors.RED}ONE@HORDE:{colors.WHITE} Requesting a caption from the AI Horde. Please wait."
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


async def generate(config, *args, **kwargs):
    api = "http://127.0.0.1:5000/generate"

    source = None
    mask = None

    try:
        if os.path.exists("/data/source.jpg"):
            with open("/data/source.jpg", "rb") as file:
                source = base64.b64encode(file.read()).decode("utf-8")
        else:
            with open("/src/static/source.jpg", "rb") as file:
                source = base64.b64encode(file.read()).decode("utf-8")

        if os.path.exists("/data/mask.jpg"):
            with open("/data/mask.jpg", "rb") as file:
                mask = base64.b64encode(file.read()).decode("utf-8")

        height = config.get("height", 256)
        width = config.get("width", 256)

        assert height % 64 == 0, "Image height should be a multiple of 64."
        assert width % 64 == 0, "Image width should be a multiple of 64."

        prompt = config.get("prompt")
        if prompt is None:
            prompt = "monolithic stone robot head with a large (wooden tree branch:1.2) growing into his face###(ugly, bad quality, worst quality, medium quality, low resolution, medium resolution, bad hands, blurry, distorted, twisted, watermark, mutant, amorphous, elongated, elastigirl, duplicate, tumor, cancer, fat, pregnant:1.3)"

        negative_prompt = config.get("negative")
        if negative_prompt is not None:
            prompt += f"###{negative_prompt}"

        data = {
            "prompt": prompt,
            "models": config.get(
                "models",
                [
                    "Dreamshaper",
                ],
            ),
            "source": source,
            "source_processing": "img2img",
            "image_is_control": False,
            "return_control_map": False,
            "height": height,
            "width": width,
            "sampler_name": config.get("sampler", "k_euler_a"),
            "steps": config.get("steps", 30),
            "control_type": config.get("control_type", "hed"),
            "denoising_strength": config.get("denoising_strength", 0.7),
            "cfg_scale": config.get("cfg_scale", 8.0),
            "clip_skip": config.get("clip_skip", 1),
            "hires_fix": config.get("hires_fix", False),
            "karras": config.get("karras", False),
            "upscale": config.get("upscale", None),
            "tis": config.get(
                "tis",
                [
                    # {"name": "72437", "strength": 1} ## BadDream
                ],
            ),
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
