import os
import re
import sys

sys.path.append("/src")
import shutil

from pypdf import PdfReader

from common import list_full_paths

# The Library: https://bafybeihwrs43mak3fn23cr5fw3vvnwi5mpyykenjgt4cinytdznnvmyjti.ipfs.nftstorage.link/
original_root = "/lab/occult/original"
original_paths = list_full_paths(original_root)
new_root = "/lab/occult/train"


def main():
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
                book = ""
                for i, page in enumerate(reader.pages):
                    os.system("clear")
                    try:
                        print(f"Archiving: {new_file}.txt (p{i})")
                        page = reader.pages[i]
                        book += page.extract_text()
                    except:
                        continue

                f.write(repair_line_breaks(book))
        except Exception as e:
            pass


def repair_line_breaks(text):
    # Handle mid-word splits with hyphenation
    text = re.sub(r"-\n", "", text)

    # Handle mid-word splits without hyphenation (lowercase letter followed by a newline and a lowercase letter)
    text = re.sub(r"([a-z])\n([a-z])", r"\1\2", text)

    # Merge lines that do not end with sentence-ending punctuation, adding a space
    text = re.sub(r"([^.!?])\n", r"\1 ", text)

    # Convert remaining single line breaks (now only at paragraph ends) to double line breaks
    text = text.replace("\n", "\n\n")

    # Normalize spaces to a single space, except for the double new lines
    text = re.sub(r"[^\S\n]+", " ", text)

    return text


if __name__ == "__main__":
    main()
