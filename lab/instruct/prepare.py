import os
import random
import shutil
import zipfile

import jsonlines

root_dir = "/lab/instruct"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    with zipfile.ZipFile(f"{root_dir}/source/data/full_data.zip", "r") as zip_ref:
        with zip_ref.open("full_data.jsonl") as file_in_zip:
            with jsonlines.Reader(file_in_zip) as f:
                instance = 0
                for line in f.iter():
                    instance = instance + 1
                    with open(
                        f"{root_dir}/train/instruction-{instance}a.md",
                        "a",
                        newline="",
                    ) as file:
                        if not line["instances"][0]["input"].startswith("None"):
                            file.write("## TRIGGER\n---\n")
                            file.write(line["instances"][0]["input"] + "\n\n")
                        file.write("## ECO\n---\n")
                        file.write(line["instruction"] + "\n\n")
                        if "reformulations" in line:
                            file.write("## ECHO\n---\n")
                            file.write(
                                line["reformulations"][0]["instruction"] + "\n\n"
                            )
                        if "constraints" in line["instances"][0]:
                            if (
                                not line["instances"][0]["constraints"]
                                .lower()
                                .startswith("none")
                            ):
                                word = random.choice(
                                    ["CONSTRAINTS", "LAW", "RULE", "DEMAND", "ACTION"]
                                )
                                file.write(f"## {word}\n---\n")
                                file.write(line["instances"][0]["constraints"] + "\n\n")
                        if not line["instances"][0]["output"].startswith("None"):
                            file.write("## PREDICTION\n---\n")
                            file.write(line["instances"][0]["output"] + "\n\n")
                    if "reformulations" in line:
                        with open(
                            f"{root_dir}/train/instruction-{instance}b.md",
                            "a",
                            newline="",
                        ) as file:
                            if not line["reformulations"][0]["input"].startswith(
                                "None"
                            ):
                                file.write("## TRIGGER\n---\n")
                                file.write(line["reformulations"][0]["input"] + "\n\n")
                            file.write("## ECO\n---\n")
                            file.write(
                                line["reformulations"][0]["instruction"] + "\n\n"
                            )
                            if not line["reformulations"][0]["output"].startswith(
                                "None"
                            ):
                                file.write("## PREDICTION\n---\n")
                                file.write(line["reformulations"][0]["output"] + "\n\n")
                        if len(line["reformulations"]) > 1:
                            with open(
                                f"{root_dir}/train/instruction-{instance}c.md",
                                "a",
                                newline="",
                            ) as file:
                                if not line["reformulations"][1]["input"].startswith(
                                    "None"
                                ):
                                    word = random.choice(["TRIGGER", "SIGNAL", "EVENT"])
                                    file.write(f"## {word}\n---\n")
                                    file.write(
                                        line["reformulations"][1]["input"] + "\n\n"
                                    )
                                file.write("## ECO\n---\n")
                                file.write(
                                    line["reformulations"][1]["instruction"] + "\n\n"
                                )
                                if not line["reformulations"][1]["output"].startswith(
                                    "None"
                                ):
                                    file.write("## PREDICTION\n---\n")
                                    file.write(
                                        line["reformulations"][1]["output"] + "\n\n"
                                    )


if __name__ == "__main__":
    main()
