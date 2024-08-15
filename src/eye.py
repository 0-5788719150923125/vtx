import asyncio
import base64
import io
import logging

import requests
from PIL import Image
from transformers import AutoImageProcessor, ViTForImageClassification

from events import consumer, producer


class Vision:
    def __init__(self):
        model = "facebook/deit-tiny-patch16-224"
        self.image_processor = AutoImageProcessor.from_pretrained(
            model, cache_dir="/data/models", device_map="cpu"
        )
        self.model = ViTForImageClassification.from_pretrained(
            model, cache_dir="/data/models", device_map="cpu"
        )

    # Function to convert and preprocess the image
    def preprocess_image(self, image, target_size=(224, 224)):
        try:
            if (
                "imgur.com" in image
                and not image.lower().endswith(".png")
                and not image.lower().endswith(".jpg")
                and not image.lower().endswith(".jpeg")
                and not image.lower().endswith(".gif")
            ):
                image = image + ".png"
            print(f"Fetching image link was: {image}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(image, stream=True, headers=headers)
            raw = None
            if response.status_code == 200:
                raw = Image.open(io.BytesIO(response.content))
            else:
                raise Exception("failed to retrieve image: ", image)
            # raw = Image.open(requests.get(image, stream=True, headers=headers).raw)
            image = raw.convert("RGB")
            image = image.resize(target_size)  # Resize to the expected dimensions
            # image = (image - 128) / 128.0  # Normalize the image (example normalization)
            return image
        except Exception as e:
            print(f"Error processing image: {e}")
            try:
                image = Image.open(image)
                image = image.resize(target_size)
                return image
            except Exception as e:
                print(f"Error processing image: {e}")
            return None

    async def analyze_image(self, image):
        try:
            url = image
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
            }
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                raise Exception(f"Error downloading image: {response.status_code}")
            data = base64.b64encode(response.content).decode("utf-8")
            producer(
                {"event": "caption_image", "image": data},
            )
            count = 0
            while count < 30:
                await asyncio.sleep(2)
                count += 1
                item = consumer("publish_caption")
                if item:
                    return item["response"]
        except Exception as e:
            logging.error(e)
        # If the AI Horde fails, use a local model
        processed = self.preprocess_image(image)
        inputs = self.image_processor(images=processed, return_tensors="pt")
        outputs = self.model(**inputs)
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        prediction = self.model.config.id2label[predicted_class_idx]
        return prediction


ctx = Vision()
