#!/usr/bin/env python3

import os
import json
import argparse
import re
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from credentials import google_api
from unidecode import unidecode

vformat = "mp4"

def rdash(s):
    s = unidecode(s)
    return re.sub('[^0-9a-zA-Z]+', '-', s)

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

def collect_talks(room_days, workdir):
    talks = []

    for room_day in room_days["room_days"]:
        room = room_day["room"]
        day = room_day["day"]

        room_day_name = f"{rdash(room)}-{rdash(day)}"
        subdir_path = os.path.join(workdir, room_day_name)

        for talk in room_day["talks"]:
            talk_title = rdash(talk["title"])
            talk_name = f"{talk_title}.{vformat}"
            thumbnail_name = f"{talk_title}.jpeg"
            talk_path = os.path.join(subdir_path, talk_name)
            thumbnail_path = os.path.join(subdir_path, thumbnail_name)
            if not os.path.isfile(talk_path):
                talk_path = None
            youtube_title = talk.get("youtube_title", talk["title"])
            youtube_desc = make_video_description(talk, talk.get("youtube_description", talk["description"]))
            validate_youtube_title(youtube_title)
            validate_youtube_description(youtube_desc)
            talks.append({
                "path": talk["path"],
                "title": youtube_title,
                "description": youtube_desc,
                "file": talk_path,
                "thumbnail": thumbnail_path,
            })

    return talks

def parse_args():
    parser = argparse.ArgumentParser(description="Takes a JSON file generated by the scale-av-cutter, and finds and uploads the videos cut by split.py to the user's Youtube account. It is usually safe to run upload.py again, since progress is by default saved to a progress file. Already-uploaded talks will be skipped, but partially uploaded talks will have to restart from scratch.")

    parser.add_argument("json", help="Path to json file of cut details")
    parser.add_argument("-w", "--workdir", default="workdir", help="Working subdirectory to find cut videos in (default: %(default)s)")
    parser.add_argument("--skip-missing-talks", action="store_true", help="Continue to upload even if some talks specified in the json are missing in workdir")
    parser.add_argument("-c", "--client", default="client_secrets.json", help="Path to client secrets file. Required if token is not valid (default: %(default)s)")
    parser.add_argument("-t", "--token", default="credentials.json", help="Path to authorization token file. If does not exist or invalid, this script will take you through the Google OAuth process (default: %(default)s)")
    parser.add_argument("--no-save-token", dest="save_token", action="store_false", help="Disable saving the authorization token to the path specified in (--token), after authorization.")
    parser.add_argument("-p", "--progress", default="progress.json", help="Path to talk upload progress file. If does not exist, all talks will be reuploaded.")
    parser.add_argument("--no-save-progress", dest="save_progress", action="store_false", help="Disable saving the uploaded status of talks to the path specified in (--progress).")
    parser.add_argument("--privacy", default="unlisted", choices=["public", "private", "unlisted"], help="Set the privacy status of uploaded videos (default: %(default)s)")
    return parser.parse_args()

def main():
    args = parse_args()

    # Collect talks
    print(f"Parsing {args.json}")
    with open(args.json) as f:
        room_days = json.load(f)
    if os.path.isfile(args.progress):
        with open(args.progress) as f:
            progress = json.load(f)
    else:
        progress = {}
    talks = collect_talks(room_days, args.workdir)
    filtered_talks = []
    for talk in talks:
        if talk["file"] is None and not args.skip_missing_talks:
            raise Exception(f"Video for {talk['title']} not found.")
        if talk["file"] is None and args.skip_missing_talks:
            print(f"WARNING: video for {talk['title']} not found. Skipping.")
            continue
        if talk["path"] in progress:
            print(f"Already uploaded: {talk['title']}.")
            continue
        print(f"Found talk: {talk['title']}")
        filtered_talks.append(talk)
    talks = filtered_talks
    print(f"Total: {len(talks)} talks to upload")
    if not talks:
        return
    # Google API
    credentials = google_api(args)

    # Upload!
    yt = build('youtube', 'v3', credentials=credentials)
    for talk in talks:
        size = os.path.getsize(talk["file"])
        print(f"Uploading \"{talk['title']}\" ({size} bytes)...")
        video = MediaFileUpload(talk['file'], chunksize=1024*1024, resumable=True)
        request = yt.videos().insert(
            part="id,snippet,status",
            body={
                "snippet": {
                    "title": talk["title"],
                    "description": talk["description"],
                },
                "status": {
                    "privacyStatus": args.privacy,
                    "selfDeclaredMadeForKids": False,
                },
            },
            media_body=video)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                n = int(status.progress() * 100)
                print(f"Uploaded {n}%...", end='\r')
        id = response['id']
        url = f"https://youtube.com/watch?v={id}"
        print("Upload complete: " + url)
        if args.save_progress:
            progress[talk["path"]] = True
            with open(args.progress, "w") as f:
                json.dump(progress, f)

        # Sets thumbnail of the video
        thumbnailPath = talk["thumbnail"]

        request = yt.thumbnails().set(
            videoId = id,
            media_body = MediaFileUpload(thumbnailPath)
        )
        request.execute()

if __name__ == "__main__":
    main()
