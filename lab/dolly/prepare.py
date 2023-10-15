import os
import shutil

from datasets import load_dataset

root_dir = "/lab/dolly"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    samples = load_dataset("databricks/databricks-dolly-15k", split="train")

    print(samples[0])

    i = 0
    for sample in samples:
        with open(f"{root_dir}/train/{i}.md", "w") as file:
            i = i + 1
            if sample["context"]:
                file.write("## CONTEXT\n---\n")
                file.write(sample["context"] + "\n\n")

            file.write("## CATEGORY\n---\n")
            file.write(sample["category"] + "\n\n")

            file.write("## INSTRUCTION\n---\n")
            file.write(sample["instruction"] + "\n\n")

            file.write("## RESPONSE\n---\n")
            file.write(sample["response"] + "\n\n")


if __name__ == "__main__":
    main()
