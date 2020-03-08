#!/usr/bin/env python3

import os
import re
import sys
import json
import subprocess
import argparse

vformat = "mp4"

def rdash(s):
    return re.sub('[^0-9a-zA-Z]+', '-', s)

def download_video(vid, outfile):
    """
    Returns boolean indicating success or failure
    """
    url = f"https://youtube.com/watch?v={vid}"
    ret = subprocess.call([
        "youtube-dl",
        "-o", outfile,  # Output
        url,            # Youtube URL
    ])
    return ret == 0

def make_cut(video, start, end, outfile):
    """
    Returns boolean indicating success or failure
    """
    ret = subprocess.call([
        "ffmpeg",
        "-y",               # Yes, overwrite
        "-ss", str(start),  # Start at closest keyframe <= start
        "-to", str(end),    # End at time end
        "-i", video,        # Input
        "-c", "copy",       # Copy stream
        outfile,            # Output
    ])
    return ret == 0

def parse_args():
    parser = argparse.ArgumentParser(description="Takes a JSON file generated by the scale-av-cutter, downloads each full day video, and cuts them into talks as specified in the file. Requires ffmpeg to be installed. It is usually safe to run split.py again, even if youtube-dl is interrupted in the middle of downloading. youtube-dl is able to skip downloaded videos, as well as resume a partial download. However, note that all talks will be re-cut via ffmpeg. This should be extremely fast, since the streams are only copied.")

    parser.add_argument("json", help="Path to json file of cut details")
    parser.add_argument("-w", "--workdir", default="workdir", help="Working subdirectory to download/split videos into. Will create if not exist (default: %(default)s)")
    parser.add_argument("-d", "--skip-download-failure", action="store_true", help="Continue even if a room day video fails to download")
    parser.add_argument("-c", "--skip-cut-failure", action="store_true", help="Continue even if ffmpeg fails to cut a talk")
    return parser.parse_args()

def main():
    args = parse_args()

    # Load JSON file
    with open(args.json) as f:
        data = json.load(f)

    # Iterate
    for room_day in data["room_days"]:
        room = room_day["room"]
        day = room_day["day"]
        vid = room_day["vid"]
        talks = room_day["talks"]

        room_day_name = f"{rdash(room)}-{rdash(day)}"
        subdir_path = os.path.join(args.workdir, room_day_name)
        video_name = f"{room_day_name}.{vformat}"
        video_path = os.path.join(subdir_path, video_name)

        # Make subdirectory
        os.makedirs(subdir_path, exist_ok=True)

        # Attempt to download video
        if not download_video(vid, outfile=video_path):
            if args.skip_download_failure:
                print(f"WARNING: Failed to download {room} {day} video {vid}. Skipping.")
                continue
            sys.exit(f"WARNING: Failed to download {room} {day} video {vid}.")

        # Split
        for talk in talks:
            title = rdash(talk["title"])
            start = talk["start"]
            end = talk["end"]
            if end <= start:
                print(f"WARNING: talk {title} has zero length video. Skipping." )

            talk_name = f"{title}.{vformat}"
            talk_path = os.path.join(subdir_path, talk_name)

            if not make_cut(video_path, start, end, outfile=talk_path):
                if args.skip_download_failure:
                    print(f"WARNING: Failed to cut clip of {title}. Skipping.")
                    continue
                sys.exit(f"ERROR: Failed to cut clip of {title}.")

if __name__ == "__main__":
    main()
