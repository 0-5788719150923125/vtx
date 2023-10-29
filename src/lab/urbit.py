import os
import time


def main(config):
    planet = config["urbit"].get("planet", False)
    while True:
        if not planet and not os.path.exists(f"/data/urbit/one.comet"):
            with open(f"/data/urbit/one.comet", "w") as file:
                pass
        else:
            # If True, expects a planet to exist under /data/urbit.
            pass

        time.sleep(66.6)


if __name__ == "__main__":
    main()
