import hashlib
import io
import json
import logging
import os
import random
import re
import secrets
import selectors
import shutil
import string
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pprint import pprint

import pytz
import requests
import yaml
from cerberus import Validator
from mergedeep import Strategy, merge

wall = "¶"
ship = ":>"

focus = os.environ["FOCUS"]

cache_path = "/tmp/torch"
os.environ["PYTORCH_KERNEL_CACHE_PATH"] = cache_path
os.environ["TOKENIZERS_PARALLELISM"] = "true"

if os.path.exists(cache_path):
    shutil.rmtree(cache_path)

os.makedirs(cache_path)

# Load configuration files from disk
with open("/src/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/env/config.yml", "r") as config_file:
        user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        if "reddit" in user_config:
            user_config["reddit"]["enabled"] = True
        config = merge({}, default_config, user_config, strategy=Strategy.REPLACE)
except Exception as e:
    logging.error(e)
    config = default_config


def colorize_yaml(yaml_dict):
    # Define ANSI color escape codes
    color_codes = {
        "red": "\033[91m",
        "reset": "\033[0m",
    }

    # Convert the YAML dictionary to a string without type tags
    yaml_text = yaml.dump(yaml_dict, default_style=None)

    # Split the YAML text into lines
    lines = yaml_text.split("\n")

    # Initialize a regular expression pattern to match lines with keys
    pattern = re.compile(r"^(\s*)([^\s:]+):(.*)(?<!\s)$")

    # Initialize a stack to keep track of whether we are within a list of dictionaries
    stack = []

    # Iterate through lines and colorize keys based on the stack
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            leading_whitespace = match.group(1)
            key = match.group(2)
            rest_of_line = match.group(3)

            # Check if we are within a list of dictionaries
            within_list_of_dicts = all(isinstance(item, dict) for item in stack)

            # Check if the key should be colored based on whether it's within a list of dicts
            if within_list_of_dicts:
                colored_key = f"{color_codes['red']}{key}{color_codes['reset']}"
                lines[i] = f"{leading_whitespace}{colored_key}:{rest_of_line}"

        # Update the stack based on indentation
        num_spaces = len(leading_whitespace)
        while len(stack) > num_spaces / 2:
            stack.pop()

        # Check if the line starts a new dictionary in a list
        if rest_of_line.startswith("- "):
            stack.append({})

    # Join the modified lines back into a single string
    colored_yaml = "\n".join(lines)

    return colored_yaml


print(colorize_yaml(config))


def validation(config):
    schema = {
        "personas": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": {
                "type": "dict",
                "schema": {
                    "bias": {"type": "integer"},
                    "persona": {"type": "string"},
                    "disposition": {"type": "list"},
                },
            },
        }
    }
    v = Validator()
    result = v.validate(config, schema)
    if not result:
        print(v.errors)
    return result


if not validation({"personas": config["personas"]}):
    raise Exception(
        "There is something wrong with the 'personas' key in your config.yml file."
    )


# Color codes
class colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    WHITE = "\033[0m"


# Return today's date
def get_current_date():
    cst = pytz.timezone("America/Chicago")  # CST
    return datetime.now(cst).strftime("%Y-%m-%d")


# Replace all newlines with even spacing
def unified_newlines(text, len=2):
    segment = "\n" * len
    while segment in text:
        text = text.replace(segment, "\n")
    return text.replace("\n", segment)


def run_shell_command(subprocess_args):
    # Start subprocess
    # bufsize = 1 means output is line buffered
    # universal_newlines = True is required for line buffering
    process = subprocess.Popen(
        subprocess_args,
        bufsize=1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
    )

    # Create callback function for process output
    buf = io.StringIO()

    def handle_output(stream, mask):
        # Because the process' output is line buffered, there's only ever one
        # line to read when this function is called
        line = stream.readline()
        buf.write(line)
        sys.stdout.write(line)

    # Register callback for an "available for read" event from subprocess' stdout stream
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, handle_output)

    # Loop until subprocess is terminated
    while process.poll() is None:
        # Wait for events and handle them with their registered callbacks
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    # Get process return code
    return_code = process.wait()
    selector.close()

    success = return_code == 0

    # Store buffered output
    output = buf.getvalue()
    buf.close()

    return (success, output)


# Get the full path of every file in a directory
def list_full_paths(directory):
    fname = []
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            fname.append(os.path.join(root, f))

    return fname


def str_to_int(seed):
    seed_bytes = seed.encode("utf-8")
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


def random_string(length=10):
    # Define the characters you want to include in the random string
    characters = (
        string.ascii_letters + string.digits
    )  # Letters (both uppercase and lowercase) and digits
    # You can customize this by adding more characters as needed

    # Use random.choices to generate the string
    random_string = "".join(random.choices(characters, k=length))

    return random_string


# Hash a string, return a name
def get_daemon(seed=random_string(length=24)):
    command = ["node", "/src/scripts/daemon.js", str(seed)]
    output = subprocess.check_output(
        command, universal_newlines=True, stderr=subprocess.STDOUT
    )
    return output.strip()


def deterministic_short_hash(input_string, length=7, seed="42"):
    # Create a hashlib sha256 object
    hasher = hashlib.sha256()

    # Update the hasher with the input string and seed
    hasher.update(seed.encode())
    hasher.update(input_string.encode())

    # Get the hexadecimal digest and truncate it to the desired length
    hex_digest = hasher.hexdigest()
    short_hash = hex_digest[:length]

    return short_hash


# Get a hash value for an entire directory
def hash_directory(path):
    sha1 = hashlib.sha1()
    for root, dirs, files in os.walk(path):
        for file in sorted(files):
            filename = os.path.join(root, file)
            try:
                with open(filename, "rb") as f:
                    while True:
                        data = f.read(65536)
                        if not data:
                            break
                        sha1.update(data)
            except Exception as e:
                logging.error(e)
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


def has_invisible_characters(text):
    # Define a regular expression to match any non-printable characters
    invisible_char_pattern = re.compile(r"[^ -~\t\n\r\f\v]+")

    # Check if the input text contains any non-printable characters
    return bool(invisible_char_pattern.search(text))


def remove_invisible_characters(text):
    # Define a regular expression to match any non-printable characters
    invisible_char_pattern = re.compile(r"[^ -~\t\n\r\f\v]+")

    # Replace all occurrences of non-printable characters with an empty string
    cleaned_text = invisible_char_pattern.sub("", text)

    while cleaned_text.startswith(" "):
        cleaned_text = cleaned_text[1:]

    return cleaned_text


def strip_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r"", text)  # no emoji


def read_from_file(path: str):
    return open(path).read()


def write_to_file(path: str, file_name: str, content: str):
    if not os.path.exists(path):
        os.makedirs(path)

    path = f"{path}/" + str(file_name)

    with open(path, "w") as file:
        file.write(content)


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
        "hour": "hours",  # Added support for "hour" and "hours"
        "hours": "hours",  # Added support for "hour" and "hours"
        "minute": "minutes",  # Added support for "minute" and "minutes"
        "minutes": "minutes",  # Added support for "minute" and "minutes"
    }

    # Convert years, months, hours, and minutes to days or hours or minutes
    if unit in ["year", "years"]:
        value *= 365
    elif unit in ["month", "months"]:
        value *= 30
    elif unit in ["hour", "hours"]:
        value *= 60  # Convert hours to minutes
        unit = "minutes"  # Update the unit to "minutes" for consistency
    elif unit in ["minute", "minutes"]:
        unit = "minutes"  # Update the unit to "minutes" for consistency

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
