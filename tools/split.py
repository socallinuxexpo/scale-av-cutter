#!/usr/bin/env python3

import os
import re
import sys
import json
import subprocess
import argparse
import shutil
from unidecode import unidecode

vformat = "mp4"

def rdash(s):
    s = unidecode(s)
    return re.sub('[^0-9a-zA-Z]+', '-', s)

def download_video(vid, outfile, container_format):
    """
    Returns boolean indicating success or failure
    """
    url = f"https://youtube.com/watch?v={vid}"

    download_format = "bestvideo+bestaudio/best"
    if container_format == "mp4":
        download_format = "mp4"

    ret = subprocess.call([
        "yt-dlp",
        "-o", outfile,          # Output filename
        "-f", download_format,  # Output container format
        url,                    # Youtube URL
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

def make_thumbnail(video, time, outfile):
    ret = subprocess.call([
        "ffmpeg",
        "-y",               # Yes, overwrite
        "-ss", str(time),   # Time of thumbnail capture
        "-i", video,        # Input
        "-frames", "1",     # Number of frames
        outfile,            # Output
    ])

    return ret == 0

def parse_args():
    parser = argparse.ArgumentParser(description="""\
Takes a JSON file generated by the scale-av-cutter, downloads each full day
video, and cuts them into talks as specified in the file. These external
executables must be installed:

- ffmpeg
- yt-dlp (actively maintained fork of youtube-dl)

split.py is idempotent, so it is usually safe to run it again even if yt-dlp is
interrupted in the middle of downloading. yt-dlp is able to skip downloaded
videos, as well as resume a partial download. However, note that all talks will
be re-cut via ffmpeg. This should be extremely fast, since the streams are only
copied.
""")

    parser.add_argument("json", help="Path to json file of cut details")
    parser.add_argument("-w", "--workdir", default="workdir", help="Working subdirectory to download/split videos into. Will create if not exist (default: %(default)s)")
    parser.add_argument("-d", "--skip-download-failure", action="store_true", help="Continue even if a room day video fails to download")
    parser.add_argument("-c", "--skip-cut-failure", action="store_true", help="Continue even if ffmpeg fails to cut a talk")
    return parser.parse_args()

def main():
    args = parse_args()

    # Check required bins
    required_bins = ["yt-dlp", "ffmpeg"]
    missing_bins = [b for b in required_bins if shutil.which(b) is None]
    if missing_bins:
        sys.exit(f"ERROR: These required executables are missing or not found in PATH: {','.join(missing_bins)}")

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
        if not download_video(vid, outfile=video_path, container_format=vformat):
            if args.skip_download_failure:
                print(f"WARNING: Failed to download {room} {day} video {vid}. Skipping.")
                continue
            sys.exit(f"WARNING: Failed to download {room} {day} video {vid}.")

        # Split
        for talk in talks:
            title = rdash(talk["title"])
            start = talk["start"]
            end = talk["end"]
            thumbnail = talk["thumbnail"]
            if end <= start:
                print(f"WARNING: talk {title} has zero length video. Skipping." )

            talk_name = f"{title}.{vformat}"
            image_name = f"{title}.png"
            talk_path = os.path.join(subdir_path, talk_name)
            thumbnail_path = os.path.join(subdir_path, image_name)

            if not make_cut(video_path, start, end, outfile=talk_path):
                if args.skip_download_failure:
                    print(f"WARNING: Failed to cut clip of {title}. Skipping.")
                    continue
                sys.exit(f"ERROR: Failed to cut clip of {title}.")

            if not make_thumbnail(video_path, thumbnail, outfile=thumbnail_path):
                if args.skip_download_failure:
                    print(f"WARNING: Failed to make thumbnail for {title}. Skipping.")
                    continue
                sys.exit(f"ERROR: Failed to make thumbnail for {title}.")

if __name__ == "__main__":
    main()
