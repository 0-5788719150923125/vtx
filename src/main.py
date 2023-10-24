import random
import time

import debugpy

time.sleep(1)

frequency = random.seed()

if __name__ == "__main__":
    debugpy.listen(("0.0.0.0", 5678))
    print("the main loop is like a constellation")
    import machine
