import json
import os
import random
import re
import shutil
import sys

sys.path.append("/src")

from common import config, get_identity, ship, wall

root_dir = "/lab/gun"


# Format Discord messages for training
def main():

    # Ensure export path exists and is clean
    if os.path.exists(f"{root_dir}/train"):
        shutil.rmtree(f"{root_dir}/train")

    os.makedirs(f"{root_dir}/train")

    pattern = r"(^|\s)(@([^\s:]+)(?::([^\s]+))?)"

    def replacer(match):
        leading = match.group(1)
        name = match.group(3)
        domain = f":{match.group(4)}" if match.group(4) else ""
        return f"{leading}<@{get_identity(f'@{name}{domain}')}>"

    successes = 0
    failures = 0
    data = None
    with open(f"{root_dir}/source/raw.json", "r") as file:
        data = json.load(file)

    data_dict = {obj["event_id"]: obj for obj in data["messages"]}

    for d in data_dict.items():

        try:

            event_id, message = d

            if message["content"].get("body") is None:
                continue

            sender = get_identity(message.get("sender"))
            content = message["content"].get("body")

            lines = content.split("\n")
            filtered_lines = [line for line in lines if not line.startswith(">")]
            content = "".join(filtered_lines)

            if message["content"].get("m.relates_to"):
                if message["content"]["m.relates_to"].get("m.in_reply_to"):
                    parent_event = message["content"]["m.relates_to"][
                        "m.in_reply_to"
                    ].get("event_id")
                    parent = data_dict[parent_event]
                    parent_sender = get_identity(parent.get("sender"))
                    parent_content = parent["content"].get("body")
                    with open(f"{root_dir}/train/room1.txt", "a") as file:
                        file.write(f"{wall}{parent_sender}{ship} {parent_content}\n")

            if message["content"].get("m.mentions"):
                if message["content"]["m.mentions"].get("user_ids"):
                    for user in message["content"]["m.mentions"]["user_ids"]:
                        identifier = f"<@{get_identity(user)}>"
                        short_user = user.split("@")[1].split("-")[0]
                        content = content.replace(user, identifier).replace(
                            short_user, identifier
                        )

            content = re.sub(pattern, replacer, content)
            data_dict[event_id]["content"]["body"] = str(content)

            with open(f"{root_dir}/train/room1.txt", "a") as file:
                file.write(f"{wall}{sender}{ship} {content}\n")

            successes += 1
        except Exception as e:
            failures += 1

        if successes % 100 == 0:
            os.system("clear")
            print("preparing GUN messages")
            print(f"{successes} successes, {failures} failures")


if __name__ == "__main__":
    main()
