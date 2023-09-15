import time
import psutil
from utils import run_shell_command


def main(config):
    run_shell_command("hugo server --source '/book' --port 42000 --noBuildLock --quiet")
    while True:
        time.sleep(6.66)
        alive = False
        for process in psutil.process_iter(["pid", "name"]):
            try:
                if process.info["name"] == "hugo":
                    status = process.status()
                    if status == "zombie":
                        continue
                    alive = True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                break
        if not alive:
            break


if __name__ == "main":
    main()
