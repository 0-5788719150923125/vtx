import os

wrangler_version = "3.23.0"


def compile_book():
    command = f"hugo --source /book --noBuildLock"
    os.system(command)


def add_site_to_ipfs():
    command = "OUTPUT=$(docker exec vtx-ipf-1 ipfs add -r /book/public --pin=false --cid-version=1 --quieter) && sed -i '$ d' /book/config.yaml && echo '      url: https://ipfs.io/ipfs/'$OUTPUT >> /book/config.yaml"
    os.system(command)
    print("added to ipfs")


def deploy_book():
    project_name = "pen"
    command = f"yes | WRANGLER_SEND_METRICS=true npx wrangler pages deploy --project-name {project_name} --directory /book/public"
    os.system(command)


if __name__ == "__main__":
    compile_book()
    add_site_to_ipfs()
    deploy_book()
