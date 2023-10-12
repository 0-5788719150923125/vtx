import git


def main():
    git.Repo.clone_from(
        "https://github.com/orhonovich/unnatural-instructions.git",
        "/lab/instruct/source",
        branch="main",
    )


if __name__ == "__main__":
    main()
