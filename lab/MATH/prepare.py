import json
import os
import shutil
import sys

sys.path.append("/src")

from common import list_full_paths

root_dir = "/lab/MATH"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    el = 0
    files = list_full_paths(f"{root_dir}/source")
    for file in files:
        if not file.endswith(".json"):
            continue
        with open(file, "r") as f:
            os.system("clear")
            print(f"parsing {el}")
            data = json.load(f)
            with open(f"{root_dir}/train/problem{el}.md", "a") as d:
                el = el + 1
                d.write("## PROBLEM\n---\n")
                d.write(data.get("problem"))
                d.write("\n\n## LEVEL\n---\n")
                d.write(data.get("level"))
                d.write("\n\n## TYPE\n---\n")
                d.write(data.get("type"))
                d.write("\n\n## SOLUTION\n---\n")
                d.write(data.get("solution"))
                d.write("\n")


if __name__ == "__main__":
    main()
