import csv
import os
import random
import shutil

root_dir = "/lab/code"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    count = 0
    with open(f"{root_dir}/source/data.csv", "r") as file:
        reader = csv.reader(file)

        for row in reader:
            if count == 0:
                count = count + 1
                continue
            with open(f"{root_dir}/train/question{count}.md", "w") as f:
                count = count + 1
                answer_type = "Wrong Answer:"
                if int(row[4]) == 1:
                    choice = random.choice(["Write", "Right"])
                    answer_type = f"{choice} Answer:"

                q_choice = random.choice(["Question", "Q"])
                string = f"""## {q_choice}:

{row[3]}

## {answer_type}

```
{row[2]}```"""

                f.write(string)


if __name__ == "__main__":
    main()
