import os
import shutil
import traceback

import jsonlines

root_dir = "/lab/qa"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    with jsonlines.open(f"{root_dir}/source/data.jsonl") as reader:
        el = 0
        for obj in reader:
            try:
                extracted = list(obj.values())
                string = f"""Q:

{extracted[0]}

A:

{extracted[1]}"""
                with open(f"{root_dir}/train/question{el}.txt", "w") as f:
                    el = el + 1

                    f.write(string)
            except Exception as e:
                print(traceback.format_exc())


if __name__ == "__main__":
    main()
