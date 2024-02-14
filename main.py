import urllib
from googleapiclient.discovery import build
from flask import render_template, request, send_from_directory, abort, redirect, make_response

from app import app, db

from models import *
app.app_context().push()
db.create_all()

from util import catch_error, expect, commit_db, input_error, access_error, error
from signxml import parse_signxml, import_talks

def room_days_query():
    return db.session.query(RoomDay)\
                .order_by(RoomDay.date)\
                .order_by(RoomDay.room)

# Match password against configured passwords
def check_level(password):
    # Yes, it's vulnerable to timing attacks. Ping the maintainer if this really matters.
    if password == app.config['EDITOR_KEY']:
        return 1
    if password == app.config['REVIEWER_KEY']:
        return 2
    if password == app.config['ADMIN_KEY']:
        return 3
    return 0

# Retrieve name and access level of user via cookies
def access(password=None, require_name=True):
    # Retrieve password via cookies if not given
    if password is None:
        password = request.cookies.get('password', None)

    # Retrieve name
    name = request.cookies.get('name', "")

    # Evaluate level.
    level = check_level(password)

    # Require name?
    if require_name and not name:
        level = 0

    return (name, level)

# Index page - login page and list of room days
@app.route('/')
def index():
    name, level = access()
    room_days = []
    fail_str = expect(request, "fail", optional=True)

    # List of login failure reasons
    fails = set()
    if fail_str:
        fails = set(fail_str.split(","))

    # Display list of room days if logged in
    if level > 0:
        room_days = room_days_query().all()

        # Evaluate statuses
        for room_day in room_days:
            needs_cut = False
            needs_review = False
            for talk in room_day.talks:
                if talk.review_status == ReviewStatus.reviewing:
                    # In edit incomplete state, needs a cut
                    if talk.edit_status == EditStatus.incomplete:
                        needs_cut = True
                    # Else, needs a review
                    else:
                        needs_review = True
            room_day.needs_cut = needs_cut
            room_day.needs_review = needs_review
            room_day.done = not needs_cut and not needs_review

    # Render
    return render_template("index.html",
                           name=name,
                           level=level,
                           fails=fails,
                           room_days=room_days)

@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('name', expires=0)
    resp.set_cookie('password', expires=0)
    return resp

@app.route('/login', methods=['POST'])
def login():
    name = expect(request, 'name', optional=True)
    password = expect(request, 'password', optional=True)
    level = check_level(password)

    fails = []
    if level == 0:
        fails.append('password')
    if not name or not name.strip() or len(name) > 32:
        fails.append('name')

    if not fails:
        resp = make_response(redirect('/'))
        resp.set_cookie('name', name)
        resp.set_cookie('password', password)
    else:
        resp = make_response(redirect('/?fail=' + ','.join(fails)))
        resp.set_cookie('name', expires=0)
        resp.set_cookie('password', expires=0)

    return resp

@app.route('/<day>/<room>')
def roomday(day, room):
    # Check for access level
    name, level = access()
    if level < 1:
        abort(403)

    room_day = room_days_query()\
                    .filter(RoomDay.room == room)\
                    .filter(RoomDay.day == day)\
                    .first()
    if not room_day:
        abort(404)

    return render_template("roomday.html",
                           name=name,
                           level=level,
                           room_day=room_day,
                           edit_statuses=[EditStatus.incomplete, EditStatus.done, EditStatus.unusable],
                           review_statuses=[ReviewStatus.reviewing, ReviewStatus.done, ReviewStatus.unusable])

@app.route('/vid', methods=['POST'])
@catch_error
@commit_db
def vid():
    # Check for access level
    _, level = access(require_name=False)
    if level < 3:
        access_error()

    room_day_id = expect(request, 'id')
    video_id = expect(request, 'vid')
    if len(video_id) > 32:
        error("Looks too long to be a YouTube video ID?")

    # Get room day
    room_day = db.session.query(RoomDay).get(room_day_id)
    if not room_day:
        input_error()

    room_day.vid = video_id
    return {}

@app.route('/comment', methods=['POST'])
@catch_error
@commit_db
def comment():
    # Check for access level
    _, level = access(require_name=False)
    if level < 3:
        access_error()

    room_day_id = expect(request, 'id')
    comment = expect(request, 'comment')
    if len(comment) > 1000:
        error("Comment cannot be >1000 characters")

    # Get room day
    room_day = db.session.query(RoomDay).get(room_day_id)
    if not room_day:
        input_error()

    room_day.comment = comment
    return {}

@app.route('/xml', methods=['POST'])
@catch_error
@commit_db
def xml():
    # Check for access level
    _, level = access(require_name=False)
    if level < 3:
        access_error()

    url = expect(request, "url")
    force_add = expect(request, "force_add", optional=True)
    if force_add:
        force_add = True
    else:
        force_add = False

    # Parse sign xml
    with urllib.request.urlopen(url) as response:
        data = response.read()
    talks = parse_signxml(data)

    # Import
    import_talks(talks, force_add)
    return {}

@app.route('/json')
@catch_error
def generate_json():
    # Check for access level
    _, level = access(require_name=False)
    if level < 1:
        access_error()

    unreviewed = expect(request, "unreviewed", optional=True)

    room_days_info = []

    room_days = room_days_query().all()
    for room_day in room_days:
        room_day_info = {
            "room": room_day.room,
            "day": room_day.day,
            "vid": room_day.vid,
            "talks": [
                {
                    "title": talk.title,
                    "description": talk.description,
                    "speakers": talk.speakers,
                    "path": talk.path,
                    "start": talk.start,
                    "end": talk.end,
                    "edit_status": talk.edit_status,
                    "review_status": talk.review_status,
                    "notes": talk.notes,
                    "thumbnail": talk.thumbnail,
                }
                for talk in room_day.talks if (
                    talk.review_status == "done" or
                    unreviewed and talk.edit_status == "done"
                )
            ],
        }
        if len(room_day_info["talks"]) > 0:
            room_days_info.append(room_day_info)

    return {"room_days": room_days_info}

@app.route('/edit', methods=['POST'])
@catch_error
@commit_db
def edit():
    # Check for access level
    name, level = access()
    if level < 1:
        access_error()

    # Fetch/validate parameters
    talk_id_str = expect(request, 'id')
    start_str = expect(request, 'start')
    end_str = expect(request, 'end')
    status = expect(request, 'status')
    thumbnail_str = expect(request, 'thumbnail')
    try:
        talk_id = int(talk_id_str)
        start = int(start_str)
        end = int(end_str)
        assert status in EditStatus.values()
        thumbnail = int(thumbnail_str)
    except:
        input_error()

    # Fetch Talk obj
    talk = db.session.query(Talk).get(talk_id)
    if not talk:
        input_error()

    # If review status is reviewed, it's not editable
    if talk.review_status != ReviewStatus.reviewing:
        error("Cannot be modified because this talk has already been reviewed")

    # Edit talk
    talk.start = start
    talk.end = end
    talk.edit_status = status
    talk.last_edited_by = name
    talk.thumbnail = thumbnail
    return {}

@app.route('/notes', methods=['POST'])
@catch_error
@commit_db
def notes():
    # Check for access level
    _, level = access()
    if level < 1:
        access_error()

    # Fetch/validate parameters
    talk_id_str = expect(request, 'id')
    notes = expect(request, 'notes')
    try:
        talk_id = int(talk_id_str)
    except:
        input_error()
    if len(notes) > 3000:
        error("Notes cannot exceed 3000 chars")

    # Fetch Talk obj
    talk = db.session.query(Talk).get(talk_id)
    if not talk:
        input_error()

    # If review status is reviewed, only reviewers and admins can edit it
    if talk.review_status != ReviewStatus.reviewing and level < 2:
        error("Cannot be modified because this talk has already been reviewed")

    # Edit talk
    talk.notes = notes
    return {}

@app.route('/review', methods=['POST'])
@catch_error
@commit_db
def review():
    # Check for access level
    name, level = access()
    if level < 2:
        access_error()

    # Fetch/validate parameters
    talk_id_str = expect(request, 'id')
    status = expect(request, 'status')
    try:
        talk_id = int(talk_id_str)
        assert status in ReviewStatus.values()
    except:
        input_error()

    # Get Talk
    talk = db.session.query(Talk).get(talk_id)
    if not talk:
        input_error()

    # Update
    talk.review_status = status
    return {}

@app.route('/auto_vids', methods=['POST'])
@catch_error
@commit_db
def auto_vids():
    # Check for access level
    _, level = access(require_name=False)
    if level < 3:
        access_error()

    # Fetch/validate parameters
    api_key = expect(request, "api_key")
    channel_id = expect(request, "channel_id")
    query = expect(request, "query", optional=True)

    # Fetch all room days
    room_days = room_days_query().all()

    # Fetch all videos from channel
    yt = build('youtube', 'v3', developerKey=api_key)
    page_token = None
    while True:
        req = yt.search().list(
            part="snippet",
            channelId=channel_id,
            type="video",
            order="date",
            maxResults=50,
            q=query,
            pageToken=page_token)
        res = req.execute()

        # Insert VID into matching room days
        done = True
        for room_day in room_days:
            if room_day.vid == "":
                for video in res['items']:
                    if video["snippet"]["title"].startswith(f"{room_day.room} {room_day.day}"):
                        room_day.vid = video["id"]["videoId"]
                        break
                else:
                    done = False
        if done:
            break

        # Next page
        if "nextPageToken" in res:
            page_token = res["nextPageToken"]
        else:
            break

    return {}

@app.route('/clear_vids', methods=['POST'])
@catch_error
@commit_db
def clear_vids():
    # Check for access level
    _, level = access(require_name=False)
    if level < 3:
        access_error()

    # Clear VID from all room days
    room_days = room_days_query().all()
    for room_day in room_days:
        room_day.vid = ""

    return {}

@app.errorhandler(403)
def forbidden(e):
    return (render_template('403.html'), 403)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static/', path)

if __name__ == '__main__':
    print("Please run using gunicorn main:app. Exiting.")
