import traceback

import jsonlines

with jsonlines.open("binary.jsonl") as reader:
    el = 0
    for obj in reader:
        try:
            extracted = list(obj.values())
            string = f"""Q:

{extracted[0]}

A:

{extracted[1]}"""
            with open(f"train/q{el}.txt", "w") as f:
                el = el + 1

                f.write(string)
        except Exception as e:
            print(traceback.format_exc())
