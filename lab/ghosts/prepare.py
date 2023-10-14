import json
import os
import random
import shutil
import string
import sys
import traceback

import contractions
import nltk
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

nltk.download("punkt")
nltk.download("stopwords")
nltk.download("wordnet")


sys.path.append("/src")

from common import get_identity, ship, wall

lemmatizer = WordNetLemmatizer()


def remove_contractions(tokenized_words):
    expanded_words = [contractions.fix(word) for word in tokenized_words]
    filtered_words = [word for word in expanded_words if wordnet.synsets(word)]
    return filtered_words


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
            content = data[instance].get("content")
            os.system("clear")
            print(f"parsing {el} of {len(list(data))}")
            el = el + 1

            with open(f"{root_dir}/train/{instance}.txt", "a") as f:
                identity = str(get_identity())
                agents = {"agent_1": identity, "agent_2": identity[::-1]}
                for turn in content:
                    agent_id = turn.get("agent")
                    message = turn.get("message")
                    f.write(f"{wall}{agents.get(agent_id)}{ship} {' '.join(message)}\n")

            with open(f"{root_dir}/train/{instance}.md", "a") as f:
                agents = {"agent_1": "< GHOST@LAN", "agent_2": "> GHOST@WAN"}
                f.write("## ECHO\n---\n```\n")
                for turn in content:
                    agent_id = agents.get(turn.get("agent"))
                    message = " ".join(turn.get("message"))
                    words = remove_contractions(word_tokenize(message))
                    filtered_words = [
                        word
                        for word in words
                        if word.lower() not in stopwords.words("english")
                        and word not in string.punctuation
                    ]
                    score = random.choice(["+", "-"]) + str(
                        round(random.uniform(0, 1), 2)
                    )
                    query = "($" + " + $".join(filtered_words).upper() + ")"
                    f.write(f"{agent_id}: {query} = {score} | {message}\n")
                f.write("```")


if __name__ == "__main__":
    main()
