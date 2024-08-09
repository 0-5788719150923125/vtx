import logging
import os
import shutil
import sys

sys.path.append("/src")
from common import get_identity, ship, wall

root_path = "/lab/EVIL"


def main():
    if os.path.exists(root_path + "/train"):
        shutil.rmtree(root_path + "/train")
    if not os.path.exists(root_path + "/train"):
        os.makedirs(root_path + "/train")
    for t in ["encoder", "decoder"]:
        for s in ["dev", "train", "test"]:
            l = (
                open(f"{root_path}/source/datasets/{t}/{t}-{s}.in", "r")
                .read()
                .split("\n")
            )
            r = (
                open(f"{root_path}/source/datasets/{t}/{t}-{s}.out", "r")
                .read()
                .split("\n")
            )
            for i, v in enumerate(l):
                try:
                    inp = get_identity()
                    out = get_identity()
                    string = f"{wall}{inp}{ship} {l[i]}\n{wall}{out}{ship} {r[i]}"
                    with open(
                        f"{root_path}/train/cmd{str(i)}.md", "w", newline=""
                    ) as file:
                        file.write(string)
                except Exception as e:
                    logging.error(e)


if __name__ == "__main__":
    main()
