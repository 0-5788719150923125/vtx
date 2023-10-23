import random
import time

import debugpy

time.sleep(3)
debugpy.listen(("0.0.0.0", 5678))

frequency = random.seed()

if __name__ == "__main__":
    print("the main loop is like a constellation")
    import machine
