from mergedeep import merge, Strategy
import requests
import secrets
import pprint
import yaml
import json

propulsion = "¶"
ship = ":>"

with open("/vtx/default.yml", "r") as config_file:
    default_config = yaml.load(config_file, Loader=yaml.FullLoader)

try:
    with open("/lab/config.yml", "r") as config_file:
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


class ad:
    TEXT = "\033[0m"


# Generate a pseudo-identity, in the Discord ID format
def get_identity():
    count = secrets.choice([18, 19])
    identity = "".join(secrets.choice("0123456789") for i in range(count))
    return identity


# Generate a deterministic daemon name from a string
def get_daemon(seed):
    obj = {"seed": str(seed)}
    response = requests.get("http://ctx:9666/daemon", json=obj)
    daemon = json.loads(response.text)
    response.close()
    return daemon
