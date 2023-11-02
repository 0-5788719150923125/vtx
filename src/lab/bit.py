import os
import time


def main(config):
    moon = config["bit"].get("moon", False)
    if not os.path.exists("/data/urbit"):
        os.mkdir("/data/urbit")
    while True:
        if not moon and not os.path.exists(f"/data/urbit/one.comet"):
            with open("/data/urbit/one.comet", "x") as file:
                pass
        elif moon:
            pass

        time.sleep(66.6)


if __name__ == "__main__":
    main()
