import urllib
from googleapiclient.discovery import build
from flask import render_template, request, send_from_directory, abort, redirect, make_response

from app import app, db

from models import *
db.create_all()

from util import catch_error, expect, commit_db, input_error, access_error, error
from signxml import parse_signxml, import_talks

def room_days_query():
    return db.session.query(RoomDay)\
                .order_by(RoomDay.date)\
                .order_by(RoomDay.room)

def access_level(password=None):
    if password is None:
        password = request.cookies.get('password', None)

    # Yes, it's vulnerable to timing attacks. Ping the maintainer if this
    # really matters.
    if password == app.config['EDITOR_KEY']:
        return 1
    if password == app.config['REVIEWER_KEY']:
        return 2
    if password == app.config['ADMIN_KEY']:
        return 3
    return 0

@app.route('/')
def index():
    level = access_level()
    room_days = []
    statuses = {}
    fail = expect(request, "fail", optional=True)

    if level > 0:
        room_days = room_days_query().all()

        for room_day in room_days:
            finished_cutting = all(talk.edit_status != EditStatus[0] for talk in room_day.talks)
            finished_reviewing = all(talk.review_status != ReviewStatus[0] for talk in room_day.talks)
            if not finished_cutting:
                status = 0
            elif not finished_reviewing:
                status = 1
            else:
                status = 2
            statuses[room_day.id] = status

    return render_template("index.html",
                           level=level,
                           fail=fail,
                           room_days=room_days,
                           statuses=statuses)

@app.route('/logout', methods=['POST'])
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('password', expires=0)
    return resp

@app.route('/login', methods=['POST'])
def login():
    password = expect(request, 'password', optional=True)
    level = access_level(password)

    if level > 0:
        resp = make_response(redirect('/'))
        resp.set_cookie('password', password)
    else:
        resp = make_response(redirect('/?fail=1'))
        resp.set_cookie('password', expires=0)

    return resp

@app.route('/<day>/<room>')
def roomday(day, room):
    # Check for access level
    if access_level() < 1:
        abort(403)

    room_day = room_days_query()\
                    .filter(RoomDay.room == room)\
                    .filter(RoomDay.day == day)\
                    .first()
    if not room_day:
        abort(404)

    return render_template("roomday.html",
                           level=access_level(),
                           room_day=room_day,
                           EditStatus=EditStatus,
                           ReviewStatus=ReviewStatus)

@app.route('/vid', methods=['POST'])
@catch_error
@commit_db
def vid():
    # Check for access level
    if access_level() < 3:
        access_error()

    room_day_id = expect(request, 'id')
    video_id = expect(request, 'vid')

    # Get room day
    room_day = db.session.query(RoomDay).get(room_day_id)
    if not room_day:
        input_error()

    room_day.vid = video_id
    return {}

@app.route('/xml', methods=['POST'])
@catch_error
@commit_db
def xml():
    # Check for access level
    if access_level() < 3:
        access_error()

    url = expect(request, 'url')

    # Parse sign xml
    with urllib.request.urlopen(url) as response:
        data = response.read()
    talks = parse_signxml(data)

    # Import
    import_talks(talks)
    return {}

@app.route('/json')
@catch_error
def generate_json():
    # Check for access level
    if access_level() < 1:
        access_error()

    approved_only = expect(request, "approved", optional=True)
    day = expect(request, "day", optional=True)

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
                }
                for talk in room_day.talks
            ],
        }
        if day and room_day_info["day"] != day:
            room_day_info["talks"] = []
        if approved_only:
            room_day_info["talks"] = list(talk for talk in room_day_info["talks"] \
                                            if (talk["edit_status"] == EditStatus[1] and
                                                talk["review_status"] == ReviewStatus[1]))
        if len(room_day_info["talks"]) > 0:
            room_days_info.append(room_day_info)

    return {"room_days": room_days_info}

@app.route('/edit', methods=['POST'])
@catch_error
@commit_db
def edit():
    # Check for access level
    if access_level() < 1:
        access_error()

    talk_id_str = expect(request, 'id')
    start_str = expect(request, 'start')
    end_str = expect(request, 'end')
    status = expect(request, 'status')
    try:
        talk_id = int(talk_id_str)
        start = int(start_str)
        end = int(end_str)
        assert status in EditStatus
    except:
        input_error()

    talk = db.session.query(Talk).get(talk_id)
    if not talk:
        input_error()

    # If review status is approved, we can't edit it
    if talk.review_status == ReviewStatus[1]:
        error("Cannot be modified because this talk has already been approved")

    talk.start = start
    talk.end = end
    talk.edit_status = status
    return {}

@app.route('/review', methods=['POST'])
@catch_error
@commit_db
def review():
    # Check for access level
    if access_level() < 2:
        access_error()

    talk_id_str = expect(request, 'id')
    status = expect(request, 'status')

    # Basic validation
    try:
        talk_id = int(talk_id_str)
        assert status in ReviewStatus
    except:
        input_error()

    # Get Talk
    talk = db.session.query(Talk).get(talk_id)
    if not talk:
        input_error()

    # If edit status is incomplete, we can't review it
    if talk.edit_status == EditStatus[0]:
        error("Cannot review an incomplete cut. If unusable, mark it as such first, and approve it.")

    # Edit
    talk.review_status = status
    return {}

@app.route('/auto_vids', methods=['POST'])
@catch_error
@commit_db
def auto_vids():
    # Check for access level
    if access_level() < 3:
        access_error()

    api_key = expect(request, "api_key")
    channel_id = expect(request, "channel_id")
    query = expect(request, "query", optional=True)

    # Fetch all room days
    room_days = room_days_query().all()

    # Fetch all videos from SCALE YT channel
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
    if access_level() < 3:
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
