import os
import shutil
import tarfile
from io import BytesIO

import requests

url = "https://people.eecs.berkeley.edu/~hendrycks/MATH.tar"

root_dir = "/lab/MATH"


def main():
    if os.path.exists(f"{root_dir}/source"):
        shutil.rmtree(f"{root_dir}/source")
    if not os.path.exists(f"{root_dir}/source"):
        os.makedirs(f"{root_dir}/source")

    response = requests.get(url)
    data = BytesIO(response.content)

    with tarfile.open(fileobj=data, mode="r") as tar:
        for member in tar.getmembers():
            if member.name.startswith("MATH"):
                member.name = os.path.relpath(member.name, "MATH")
                tar.extract(member, f"{root_dir}/source")


if __name__ == "__main__":
    main()
