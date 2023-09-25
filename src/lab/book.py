import time
import psutil
from utils import run_shell_command


def main(config):
    while True:
        alive = False
        for process in psutil.process_iter(["pid", "name"]):
            if process.info["name"] != "hugo":
                continue
            if process.status() == "zombie":
                continue
            alive = True
        time.sleep(6.66)
        if not alive:
            run_shell_command(
                "hugo server --source '/book' --port 42000 --noBuildLock --quiet"
            )


if __name__ == "main":
    main()
