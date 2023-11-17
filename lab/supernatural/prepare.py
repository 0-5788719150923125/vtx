import os
import random
import shutil
import sys

import datasets

sys.path.append("/src")

from common import get_identity, ship, wall

root_dir = "/lab/supernatural"
num_samples = 10000


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    dataset = datasets.load_dataset(
        "Muennighoff/natural-instructions",
        split="train",
        streaming=True,
        cache_dir="/data/pile",
    )

    count = 0
    while count <= num_samples:
        os.system("clear")
        print(f"preparing {count} samples")
        ds = dataset.shuffle(seed=random.randint(0, 2**31), buffer_size=1)
        d = next(iter(ds))
        with open(f"{root_dir}/train/{d.get('id')}.txt", "w") as file:
            human = get_identity()
            robot = get_identity()
            file.write(f"{wall}{human}{ship} {d.get('definition')}\n")
            file.write(f"{wall}{human}{ship} {d.get('inputs')}\n")
            file.write(f"{wall}{robot}{ship} {d.get('targets')}")
        count += 1


if __name__ == "__main__":
    main()
