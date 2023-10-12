import csv
import os
import random
import shutil

root_dir = "/lab/logic"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    with open(f"{root_dir}/source/AND.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"{root_dir}/train/AND{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["and", "AND", "&&"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")

    with open(f"{root_dir}/source/IMPLICATION.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(
                f"{root_dir}/train/IMPLICATION{line[0]}.txt", "w", newline=""
            ) as file:
                file.write(
                    f"if {line[2]} is sufficient for {line[1]}, then {line[1]} implies {line[2]} is {line[3]}"
                )

    with open(f"{root_dir}/source/NOT.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"{root_dir}/train/NOT{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["is not", "is NOT", "!="])
                file.write(f"if X1 is {line[1]}, then Target {operator} {line[2]}")

    with open(f"{root_dir}/source/OR.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"{root_dir}/train/OR{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["or", "OR", "||"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")

    with open(f"{root_dir}/source/XOR.csv", "r", newline="") as file:
        lines = csv.reader(file)
        for line in lines:
            with open(f"{root_dir}/train/XOR{line[0]}.txt", "w", newline="") as file:
                operator = random.choice(["xor", "XOR", "exclusive or"])
                file.write(f"if {line[1]} {operator} {line[2]}, then {line[3]}")


if __name__ == "__main__":
    main()
