import os
import shutil


# Get the full path of every file in a directory and delete .ckpt files
def delete_ckpt_files(directory):
    for root, d_names, f_names in os.walk(directory):
        for f in f_names:
            if f.endswith(".ckpt"):
                file_path = os.path.join(root, f)
                os.remove(file_path)
                print(f"Deleted: {file_path}")


delete_ckpt_files("/data/adapters")
delete_ckpt_files("/data/models")

shutil.rmtree(f"/data/logs", ignore_errors=True)
shutil.rmtree(f"/data/pile", ignore_errors=True)
