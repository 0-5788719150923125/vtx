import os


def convert_video_to_ascii():
    command = f"/src/edge/mediatoascii --video-path /data/input.mp4 -o /data/output.mp4 --scale-down 16.0 --overwrite"
    os.system(command)


if __name__ == "__main__":
    convert_video_to_ascii()
