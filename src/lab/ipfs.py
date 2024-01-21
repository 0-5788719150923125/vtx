import os


def main(config):
    c_command = "ipfs pin add --recursive --progress bafybeicnfzilqmzw5eo7zokf6xjl2rpxbwl4lb7lxwn3xitvzzqgsh3eyq"
    command = f"docker exec vtx-ipf-1 {c_command}"
    os.system(command)


if __name__ == "__main__":
    main()
