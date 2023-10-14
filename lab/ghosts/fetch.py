import os
import shutil

import requests

urls = [
    "https://enriched-topical-chat.s3.amazonaws.com/train.json",
    "https://enriched-topical-chat.s3.amazonaws.com/valid_freq.json",
    "https://enriched-topical-chat.s3.amazonaws.com/valid_rare.json",
    "https://enriched-topical-chat.s3.amazonaws.com/test_freq.json",
    "https://enriched-topical-chat.s3.amazonaws.com/test_rare.json",
]

root_path = "/lab/ghosts"


def main():
    if os.path.exists(f"{root_path}/source"):
        shutil.rmtree(f"{root_path}/source")
    if not os.path.exists(f"{root_path}/source"):
        os.makedirs(f"{root_path}/source")

    for url in urls:
        file_name = url.split("/")[-1]

        response = requests.get(url)

        if response.status_code == 200:
            with open(f"{root_path}/source/{file_name}", "wb") as file:
                file.write(response.content)

    print(f"JSON data downloaded and saved to {root_path}/source")


if __name__ == "__main__":
    main()
