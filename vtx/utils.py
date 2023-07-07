from mergedeep import merge, Strategy
import requests
import shutil
import secrets
import random
import pprint
import yaml
import json
import hashlib
import os
import statistics
import websocket

propulsion = "¶"
ship = ":>"

cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path
os.environ["TOKENIZERS_PARALLELISM"] = "true"

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

# Load configuration files from disk
with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/vtx/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

pprint.pprint(config)


# Color codes before
class bc:
    FOLD = "\033[94m"
    ROOT = "\033[92m"
    CORE = "\033[91m"


# Color codes after
class ad:
    TEXT = "\033[0m"


# Get the full path of every file in a directory
def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


# Generate a pseudo-identity, in the Discord ID format
def get_identity():
    count = secrets.choice([17, 18])
    leading = secrets.choice("123456789")
    identity = leading + "".join(secrets.choice("0123456789") for i in range(count))
    return identity


def get_daemon(seed):
    ws = websocket.WebSocket()
    ws.connect("ws://localhost:9666/wss")
    ws.send(json.dumps({"seed": seed}))
    response = ws.recv()
    ws.close()
    return json.loads(response)["name"]


# Get a hash value for an entire directory
def hash_directory(path):
    sha1 = hashlib.sha1()
    for root, dirs, files in os.walk(path):
        for file in sorted(files):
            filename = os.path.join(root, file)
            with open(filename, "rb") as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
    return sha1.hexdigest()


# Fetch a random number
def get_quantum_seed(length: int = 23, data_type: str = "uint8"):
    try:
        response = requests.get(
            f"https://qrng.anu.edu.au/API/jsonI.php?length={str(length)}&type={data_type}"
        )
        bullet = json.loads(response.text)
        if bullet["success"] == True:
            return [True, statistics.median(bullet["data"])]
        raise Exception("failed to connect to the mainframe")
    except:
        return [False, random.randint(0, 2**32 - 1)]


# Write to a log file
def write_log_file(dir: str, content: str):
    if not os.path.exists(dir):
        os.makedirs(dir)

    num = 0
    path = f"{dir}/test-" + str(num) + ".md"

    while os.path.exists(path):
        num = num + 1
        path = f"{dir}/test-" + str(num) + ".md"
    with open(path, "w") as file:
        file.write(content)


bullets = {
    "⠠",
    "⠏",
    "⠲",
    "⠢",
    "⠐",
    "⠕",
    "⠥",
    "⠭",
    "⠞",
    "⠱",
    "⠟",
    "⠒",
    "⠇",
    "⠙",
    "⠮",
    "⠪",
    "⠑",
    "⠷",
    "⠿",
    "⠊",
    "⠂",
    "⠅",
    "⠡",
    "⠬",
    "⠝",
    "⠰",
    "⠽",
    "⠻",
    "⠧",
    "⠃",
    "⠼",
    "⠹",
    "⠌",
    "⠵",
    "⠄",
    "⠎",
    "⠫",
    "⠳",
    "⠯",
    "⠗",
    "⠉",
    "⠁",
    "⠛",
    "⠸",
    "⠋",
    "⠺",
    "⠔",
    "⠓",
    "⠜",
    "⠆",
    "⠍",
    " ",
    "\n",
}
