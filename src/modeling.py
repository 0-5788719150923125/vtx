import os
import time

import yaml

from common import merge_dict


def get_ship_class(config, focus):
    """Merge model designs into the global configuration."""

    print("loading ship design")
    time.sleep(5)
    c = config[focus].get("class")
    with open(f"/src/hangar/{c}.yml", "r") as file:
        class_config = yaml.load(file, Loader=yaml.FullLoader)
        spec = {focus: class_config}
        print(spec)
        print(f"class {c} was found")
        time.sleep(2)
        return merge_dict(spec, config)
