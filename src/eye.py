import io

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image
from transformers import AutoImageProcessor, ViTForImageClassification


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

    def analyze_image(self, image):
        # url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        processed = self.preprocess_image(image)
        # image = Image.open("/data/meme.webp")

        inputs = self.image_processor(images=processed, return_tensors="pt")
        outputs = self.model(**inputs)
        logits = outputs.logits
        # model predicts one of the 1000 ImageNet classes
        predicted_class_idx = logits.argmax(-1).item()
        prediction = self.model.config.id2label[predicted_class_idx]
        return prediction


ctx = Vision()

# ctx = cortex(config[focus], config["personas"], config["disposition"], focus)
# reload_interval = config[focus].get("reload_interval", 0)
# if reload_interval > 0:
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(
#         cortex,
#         args=(
#             config[focus],
#             config["personas"],
#             config["disposition"],
#             focus,
#         ),
#         trigger="interval",
#         minutes=reload_interval,
#     )
#     scheduler.start()
