import urllib
from flask import render_template, request, send_from_directory, abort

from app import app, db

from models import *
db.create_all()

from util import catch_error, expect, commit_db, input_error, admin_error, error
from signxml import parse_signxml, import_talks

def room_days_query():
    return db.session.query(RoomDay)\
                .order_by(RoomDay.date)\
                .order_by(RoomDay.room)\
                .join(Talk)\
                .order_by(Talk.sched_start)

def is_admin():
    if 'password' not in request.cookies:
        return False
    if request.cookies['password'] != app.config['ADMIN_KEY']:
        return False
    return True

@app.route('/')
def index():
    room_days = room_days_query().all()

    statuses = {}
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

    return render_template("index.html", room_days=room_days, statuses=statuses, is_admin=is_admin())

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/<day>/<room>')
def roomday(day, room):
    room_day = room_days_query()\
                    .filter(RoomDay.room == room)\
                    .filter(RoomDay.day == day)\
                    .first()
    if not room_day:
        abort(404)

    return render_template("roomday.html", room_day=room_day, EditStatus=EditStatus, ReviewStatus=ReviewStatus, is_admin=is_admin())

@app.route('/vid', methods=['POST'])
@catch_error
@commit_db
def vid():
    room_day_id = expect(request, 'id')
    video_id = expect(request, 'vid')

    # Check for admin permissions
    if not is_admin():
        admin_error()

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
    url = expect(request, 'url')

    # Check for admin permissions
    if not is_admin():
        admin_error()

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
    talk_id_str = expect(request, 'id')
    status = expect(request, 'status')

    # Check for admin permissions
    if not is_admin():
        admin_error()

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

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static/', path)

if __name__ == '__main__':
    print("Please run using gunicorn main:app. Exiting.")
