import json
import os
import random
import shutil
import sys
import traceback

sys.path.append("/src")

from common import get_identity, ship, wall

root_dir = "/lab/QA"
duplicates = 3


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    with open(f"{root_dir}/source/data.jsonl", "r") as file:
        json_lines = [json.loads(line) for line in file]
        el = 0
        count = 0
        while count < duplicates:
            random.shuffle(json_lines)
            for obj in json_lines:
                try:
                    extracted = list(obj.values())
                    string = f"""{wall}{get_identity()}{ship} {extracted[0]}
{wall}{get_identity()}{ship} {extracted[1]}"""
                    with open(f"{root_dir}/train/question{el}.txt", "w") as f:
                        el = el + 1

                        f.write(string)
                except Exception as e:
                    print(traceback.format_exc())
            count += 1


if __name__ == "__main__":
    main()
