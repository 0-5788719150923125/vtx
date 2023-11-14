import os
import shutil

import requests

url = "https://www.kaggle.com/datasets/polartech/us-college-textbooks-and-courses-dataset/download?datasetVersionNumber=1"

root_path = "/lab/college"


def main():
    if os.path.exists(f"{root_path}/source"):
        shutil.rmtree(f"{root_path}/source")
    if not os.path.exists(f"{root_path}/source"):
        os.makedirs(f"{root_path}/source")

    response = requests.get(url)

    if response.status_code == 200:
        with open(f"{root_path}/source/data.zip", "wb") as file:
            file.write(response.content)

    print(f"JSON data downloaded and saved to {root_path}/source")


if __name__ == "__main__":
    main()
