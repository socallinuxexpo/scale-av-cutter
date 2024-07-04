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

    # Directly from yt-dlp manual
    # Download the best mp4 video available, or the best video if no mp4 available
    #  $ yt-dlp -f "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4] / bv*+ba/b"
 
    download_format = f"bv*[ext={container_format}]+ba[ext=m4a]/b[ext={container_format}] / bv*+ba/b"
    
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
        "-frames:v", "1",   # Number of frames
        "-qscale:v", "2",   # Quality of JPEG
        outfile,            # Output
    ])

    return ret == 0

def validate_youtube_title(title):
    # https://developers.google.com/youtube/terms/required-minimum-functionality#data-requirements
    if len(title) > 100:
        raise Exception(f"Title '{title}' is longer than 100 characters. Modify JSON to include a valid youtube_title field.")
    if "<" in title or ">" in title:
        raise Exception(f"Title '{title}' contains an invalid character. Modify JSON to include a valid youtube_title field.")

def validate_youtube_description(desc):
    # https://developers.google.com/youtube/terms/required-minimum-functionality#data-requirements
    if len(desc.encode('utf-8')) > 5000:
        raise Exception(f"Description '{desc}' is longer than 5000 bytes. Modify JSON to include a valid youtube_description field.")
    if "<" in desc or ">" in desc:
        raise Exception(f"Description '{desc}' contains an invalid character. Modify JSON to include a valid youtube_description field.")

def make_video_description(talk, desc):
    link = "https://www.socallinuxexpo.org" + talk["path"]
    return f"""\
Talk by {talk["speakers"]}

{link}

{desc}"""

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
            image_name = f"{title}.jpeg"
            talk_path = os.path.join(subdir_path, talk_name)
            thumbnail_path = os.path.join(subdir_path, image_name)

            youtube_desc = make_video_description(talk, talk["description"])
            youtube_title = talk.get("youtube_title", talk["title"])
            validate_youtube_title(youtube_title)
            validate_youtube_description(youtube_desc)

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
