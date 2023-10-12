import os

import requests
from bs4 import BeautifulSoup


def compile_book():
    command = f"hugo --source /book --noBuildLock"
    os.system(command)


def deploy_book():
    project_name = "pen"
    command = f"WRANGLER_SEND_METRICS=true wrangler pages deploy --project-name {project_name} --directory /book/public"
    os.system(command)


def convert_video_to_ascii():
    command = f"/src/scripts/mediatoascii --video-path /src/scripts/input.mp4 -o /src/scripts/output.mp4 --scale-down 16.0 --overwrite"
    os.system(command)


def upload_model_via_scp():
    command = f"scp -i /home/crow/Documents/creds/Oracle/one.key -r ./src/adapters/mind opc@129.159.66.224:/home/opc/vtx/src/adapters/mind"
    os.system(command)


# Grab all internal links from a web page
def crawl(site="https://ink.university"):
    html = requests.get(site).content
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    internal_links = []
    for link in links:
        href = link.get("href")
        if href.startswith("/"):
            internal_links.append(site + href)
    print(internal_links)
    return internal_links
