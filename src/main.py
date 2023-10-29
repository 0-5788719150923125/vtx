import os
import random
import time

if __name__ == "__main__":
    frequency = random.seed()
    if os.environ.get("DEV_MODE", "false") == "true":
        import debugpy

        time.sleep(1)
        debugpy.listen(("0.0.0.0", 5678))

    print("the main loop is like a constellation")
    import machine
