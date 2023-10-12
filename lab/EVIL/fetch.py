import git


def main():
    git.Repo.clone_from(
        "https://github.com/dessertlab/EVIL.git", "/lab/EVIL/source", branch="main"
    )


if __name__ == "__main__":
    main()
