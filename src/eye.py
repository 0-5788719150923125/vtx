import asyncio
import base64
import io
import time

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image
from transformers import AutoImageProcessor, ViTForImageClassification

from events import consumer, producer


class Vision:
    def __init__(self):
        model = "facebook/deit-tiny-patch16-224"
        self.image_processor = AutoImageProcessor.from_pretrained(
            model, cache_dir="/data/models"
        )
        self.model = ViTForImageClassification.from_pretrained(
            model, cache_dir="/data/models"
        )

    # Function to convert and preprocess the image
    def preprocess_image(self, image, target_size=(224, 224)):
        try:
            if "imgur.com" in image:
                image = image + ".png"
            raw = Image.open(requests.get(image, stream=True).raw)
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
            response = requests.get(url)
            if response.status_code != 200:
                raise Exception(f"Error downloading image: {response.status_code}")
            data = base64.b64encode(response.content).decode("utf-8")
            producer(
                {"event": "caption_image", "image": data},
            )
            count = 0
            while count < 30:
                await asyncio.sleep(6.66)
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
