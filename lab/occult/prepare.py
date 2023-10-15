import os
import sys

sys.path.append("/src")
import shutil

from pypdf import PdfReader

from common import list_full_paths

# The Library: https://bafybeihwrs43mak3fn23cr5fw3vvnwi5mpyykenjgt4cinytdznnvmyjti.ipfs.nftstorage.link/
original_root = "/lab/occult/original"
original_paths = list_full_paths(original_root)
new_root = "/lab/occult/train"

if os.path.exists(new_root):
    shutil.rmtree(new_root)
if not os.path.exists(new_root):
    os.makedirs(new_root)

for file in original_paths:
    new_file = file.replace(original_root, new_root)

    directory_path = os.path.dirname(new_file)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

    try:
        if not file.lower().endswith(".pdf"):
            shutil.copy(file, new_file)
            continue

        reader = PdfReader(file)

        with open(f"{new_file}.txt", "a") as f:
            for i, page in enumerate(reader.pages):
                os.system("clear")
                print(f"Archiving: {new_file}.txt (p{i})")

                try:
                    page = reader.pages[i]
                    text = page.extract_text()

                    f.write(text)
                except:
                    pass
    except:
        pass
