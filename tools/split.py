#!/usr/bin/env python3

import re
import sys
import json
import subprocess
import argparse

def rdash(s):
    return re.sub('[^0-9a-zA-Z]+', '-', s)

def download_video(vid, room, day):
    """
    Returns path (name) of video file if successful download, or None if failed
    to download
    """
    vformat="mp4"
    name=f"{rdash(room)}-{rdash(day)}.{vformat}"
    url=f"https://youtube.com/watch?v={vid}"
    ret = subprocess.call([
        "youtube-dl",
        "-f", vformat,  # Format to download
        "-o", name,     # Output
        url,
    ])
    if ret != 0:
        return None
    return name

def make_cut(video, title, start, end):
    """
    Returns path (name) of clip if successful cut, or None if failed
    """
    vformat="mp4"
    name=f"{rdash(title)}.{vformat}"
    ret = subprocess.call([
        "ffmpeg",
        "-y",               # Yes, overwrite
        "-ss", str(start),  # Start at closest keyframe <= start
        "-to", str(end),    # End at time end
        "-i", video,        # Input
        "-c", "copy",       # Copy stream
        name,
    ])
    if ret != 0:
        return None
    return name

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("json", help="Path to json file of cut details")
    parser.add_argument("-k", "--keep", action="store_true", default=False,
                        help="Keep all downloaded full videos (default: %(default)s)")
    return parser.parse_args()

def main():
    args = parse_args()

    with open(args.json) as f:
        data = json.load(f)
    for room_day in data:
        room = room_day["room"]
        day = room_day["day"]
        vid = room_day["vid"]
        cuts = room_day["cuts"]

        video = download_video(vid, room, day)
        if not video:
            sys.stderr.write(f"ERROR: Failed to download {room} {day} video {vid}. Skipping.\n")
            continue

        for cut in cuts:
            title = rdash(cut["title"])
            start = cut["start"]
            end = cut["end"]
            clip = make_cut(video, title, start, end)
            if not clip:
                sys.stderr.write(f"ERROR: Failed to cut clip of {title}. Skipping.\n")
                continue

if __name__ == "__main__":
    main()
