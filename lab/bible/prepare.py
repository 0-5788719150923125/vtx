import csv
import os
import random
import shutil
import sys

sys.path.append("/src")

root_dir = "/lab/bible"

from common import list_full_paths


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    files = list_full_paths(f"{root_dir}/source")
    count = 0
    for file in files:
        with open(file, mode="r") as f:
            reader = csv.DictReader(f)
            # batch = random.randint(1, 5)
            # book = None
            for row in reader:
                os.system("clear")
                print(f"writing {count}")
                book = row["Book"]
                chapter = row["Chapter"]
                verse = row["Verse"]
                text = row["Text"]

                with open(f"{root_dir}/train/excerpt{count}.md", "a") as target:
                    target.write(f"{book} {chapter}:{verse} - {text}")
                    count += 1


if __name__ == "__main__":
    main()
