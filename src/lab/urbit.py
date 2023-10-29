import os
import time


def main(config):
    planet = config["urbit"].get("planet", False)
    if not os.path.exists("/data/urbit"):
        os.mkdir("/data/urbit")
    while True:
        if not planet and not os.path.exists(f"/data/urbit/one.comet"):
            with open("/data/urbit/one.comet", "x") as file:
                pass
        elif planet and os.path.exists("/data/urbit/one"):
            pass

        time.sleep(66.6)


if __name__ == "__main__":
    main()
