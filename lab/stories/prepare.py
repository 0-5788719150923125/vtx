import os
import shutil

from datasets import load_dataset

root_dir = "/lab/stories"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    samples = load_dataset(
        "roneneldan/TinyStories", split="train", cache_dir=f"{root_dir}/source"
    )

    print(samples)

    i = 0
    with open(f"{root_dir}/train/book.md", "a") as file:
        for sample in samples:
            i = i + 1
            if i > 100_000:
                break
            file.write(sample["text"] + "\n\n")


if __name__ == "__main__":
    main()
