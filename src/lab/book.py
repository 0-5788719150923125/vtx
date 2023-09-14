import time
from utils import run_shell_command


def main(config):
    command = run_shell_command(
        "hugo server --source '/book' --port 42000 --noBuildLock --quiet"
    )
    while True:
        time.sleep(6.66)


if __name__ == "main":
    main()
