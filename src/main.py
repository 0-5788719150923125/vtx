import os
import random
import time

mode = os.environ["DEV_MODE"]

if __name__ == "__main__":
    if mode is not None and mode == "true":
        import debugpy

        time.sleep(1)
        frequency = random.seed()
        debugpy.listen(("0.0.0.0", 5678))

    print("the main loop is like a constellation")
    import machine
