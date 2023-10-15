import os
import shutil

from datasets import load_dataset

root_dir = "/lab/phi"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    samples = load_dataset(
        "open-phi/textbooks", split="train", cache_dir=f"{root_dir}/source"
    )

    print(samples)

    i = 0
    for sample in samples:
        i = i + 1
        with open(f"{root_dir}/train/textbook{i}.md", "a") as file:
            file.write(f"# (title)\n## RECORD\n---\n```\n")
            file.write(f"Topic: {sample['topic']}\n")
            file.write(f"Field: {sample['field']}\n")
            file.write(f"Subfield: {sample['subfield']}\n")
            if sample["concepts"] != "[]":
                file.write(f"Concepts: {sample['concepts']}\n")
            file.write("```\n\n")
            file.write(sample["outline"])
            file.write(sample["markdown"])


if __name__ == "__main__":
    main()
