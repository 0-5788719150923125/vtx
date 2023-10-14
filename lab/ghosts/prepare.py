import json
import os
import shutil
import sys
import traceback

sys.path.append("/src")

from common import get_identity, ship, wall

root_dir = "/lab/ghosts"


def main():
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")
    if not os.path.exists(f"{root_dir}/train"):
        os.makedirs(f"{root_dir}/train")

    with open(f"{root_dir}/source/train.json", "r") as file:
        el = 0
        data = json.load(file)
        for instance in list(data):
            agents = {"agent_1": get_identity(), "agent_2": get_identity()}

            content = data[instance].get("content")

            from pprint import pprint

            pprint(content)
            with open(f"{root_dir}/train/{instance}.txt", "a") as f:
                for turn in content:
                    agent_id = turn.get("agent")
                    message = turn.get("message")
                    f.write(
                        f"{wall}{agents.get(agent_id)}{ship} {' '.join(message)}\n\n"
                    )

            break


#         for obj in reader:
#             try:
#                 extracted = list(obj.values())
#                 string = f"""Q:

# {extracted[0]}

# A:

# {extracted[1]}"""
#                 with open(f"{root_dir}/train/question{el}.txt", "w") as f:
#                     el = el + 1

#                     f.write(string)
#             except Exception as e:
#                 print(traceback.format_exc())


if __name__ == "__main__":
    main()
