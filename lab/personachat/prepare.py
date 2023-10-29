import os
import shutil

from datasets import load_dataset

root_dir = "/lab/personachat"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    samples = load_dataset(
        "bavard/personachat_truecased", split="train", cache_dir=f"{root_dir}/source"
    )

    print(samples)

    def chunking(examples):
        inputs = [
            "\n-----\n".join(history) + "\n-----\n" + candidate
            for history, candidates in zip(examples["history"], examples["candidates"])
            for candidate in candidates
        ]
        return {"chunks": inputs}

    def tokenize(examples):
        outputs = {
            "input_ids": tokenizer(
                examples["chunks"], padding="max_length", truncation=True
            )["input_ids"]
        }
        outputs["labels"] = outputs["input_ids"]
        return outputs

    dataset = samples.map(chunking, batched=True, remove_columns=samples.column_names)
    # .map(tokenize, batched=True, remove_columns=["chunks"])

    i = 0
    for sample in dataset:
        i = i + 1
        print(sample)
        if i == 20:
            break
        # with open(f"{root_dir}/train/textbook{i}.md", "a") as file:
        #     file.write(f"# (title)\n## RECORD\n---\n```\n")
        #     file.write(f"Topic: {sample['topic']}\n")
        #     file.write(f"Field: {sample['field']}\n")
        #     file.write(f"Subfield: {sample['subfield']}\n")
        #     if sample["concepts"] != "[]":
        #         file.write(f"Concepts: {sample['concepts']}\n")
        #     file.write("```\n\n")
        #     file.write(sample["outline"])
        #     file.write(sample["markdown"])


if __name__ == "__main__":
    main()
