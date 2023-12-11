import os
import time


def main(config):
    planet = config["urbit"].get("planet", False)
    moon = config["urbit"].get("moon", False)
    os.makedirs("/data/urbit", exist_ok=True)
    if os.path.exists(f"/data/urbit/one"):
        if len(os.listdir("/data/urbit/one")) == 0:
            os.rmdir("/data/urbit/one")
    while True:
        if moon or planet:
            pass
        # Create a file, which will launch a comet.
        elif not os.path.exists(f"/data/urbit/one.comet"):
            with open("/data/urbit/one.comet", "x") as file:
                pass

        time.sleep(66.6)


if __name__ == "__main__":
    main()
