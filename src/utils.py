from mergedeep import merge, Strategy
import requests
import shutil
import secrets
import random
import string
from pprint import pprint
import yaml
import json
import hashlib
import os
import websocket
import time
import re
from datetime import datetime, timedelta

propulsion = "¶"
ship = ":>"

cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path
os.environ["TOKENIZERS_PARALLELISM"] = "true"

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

# Load configuration files from disk
with open("./default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("./config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except:
    config = default_config

pprint(config)


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

def str_to_int(seed):
  seed_bytes = seed.encode('utf-8')
  seed_int = hashlib.sha256(seed_bytes).hexdigest()
  seed_int = int(seed_int, 16)
  return seed_int

def make_random_deterministic(seed):
  seed_int = str_to_int(str(seed))[:10]
  random.seed(seed_int)

# Generate a pseudo-identity, in the Discord ID format
def get_identity(seed=None):

    if seed is not None:
        random.seed(seed)

    count = random.choice([17, 18])
    leading = random.choice("123456789")
    identity = leading + "".join(random.choice("0123456789") for _ in range(count))

    random.seed()
    
    return identity


# Hash a string, return a name
def get_daemon(seed):
    ws = websocket.WebSocket()
    ws.connect("ws://ctx:9666/wss")
    ws.send(json.dumps({"seed": seed}).encode("utf-8"))
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

last_query_time = 0
cached_value = None

# Generate an integer by using NIST's beacon service
def nist_beacon():
    global last_query_time
    global cached_value
    current_time = time.time()
    try:
        if current_time - last_query_time >= 60 or cached_value is None:
            response = requests.get(
                "https://beacon.nist.gov/beacon/2.0/pulse/last", timeout=1
            )
            data = response.json()
            local_random_value = data["pulse"]["localRandomValue"]
            hash_object = hashlib.sha256(local_random_value.encode())
            hashed_value = int.from_bytes(hash_object.digest(), byteorder="big") % (
                1 << 32
            )
            cached_value = [True, hashed_value]
            last_query_time = current_time
        else:
            cached_value = [False, random.randint(0, 2**32 - 1)]
    except Exception as e:
        cached_value = [False, random.randint(0, 2**32 - 1)]

    return cached_value


def strip_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)  # no emoji


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

def read_from_file(path: str):
    return open(path).read()

def write_to_file(path: str, file_name: str, content: str):
    if not os.path.exists(path):
        os.makedirs(path)

    path = f"{path}/" + str(file_name)

    with open(path, "w") as file:
        file.write(content)

def random_string(length=10):
    # Define the characters you want to include in the random string
    characters = string.ascii_letters + string.digits  # Letters (both uppercase and lowercase) and digits
    # You can customize this by adding more characters as needed

    # Use random.choices to generate the string
    random_string = ''.join(random.choices(characters, k=length))

    return random_string

# Take a relative date in string format, and return the formatted value
def get_past_datetime(time_description):
    # Split the input string into value and unit
    value, unit = time_description.split()

    # Convert the value to an integer
    value = int(value)

    # Define a dictionary to map units to timedelta attributes
    time_units = {
        "year": "days",
        "years": "days",
        "month": "days",
        "months": "days",
        "week": "weeks",
        "weeks": "weeks",
        "day": "days",
        "days": "days",
    }

    # Convert years and months to days
    if unit in ["year", "years"]:
        value *= 365
    elif unit in ["month", "months"]:
        value *= 30

    # Calculate the timedelta based on the unit
    delta_unit = time_units[unit]
    delta = timedelta(**{delta_unit: value})

    # Get the current date and time
    current_datetime = datetime.now()

    # Calculate the past date and time
    past_datetime = current_datetime - delta

    # Format the past date and time
    formatted_date_time = past_datetime.strftime("%Y-%m-%d %H:%M")

    return formatted_date_time


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
