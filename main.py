import urllib
from flask import render_template, request, send_from_directory

from app import app, db

from models import *
db.create_all()

from util import catch_error, expect, commit_db, input_error
from signxml import parse_signxml, import_talks

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/edit/<day>/<room>')
def roomday(day, room):
    room_day = db.session.query(RoomDay)\
                    .filter(RoomDay.room == room)\
                    .filter(RoomDay.day == day)\
                    .first()
    if not room_day:
        abort(404)

    cuts = db.session.query(Cut)\
                    .filter(Cut.room_day_id == room_day.id)\
                    .all()
    return render_template("roomday.html", room_day=room_day, cuts=cuts, EditStatus=EditStatus)

@app.route('/xml', methods=['POST'])
@catch_error
@commit_db
def xml():
    url = expect(request, 'url')

    with urllib.request.urlopen(url) as response:
        data = response.read()
    talks = parse_signxml(data)
    import_talks(talks)
    return {}

@app.route('/edit', methods=['POST'])
@catch_error
@commit_db
def edit():
    cut_id_str = expect(request, 'id')
    start_str = expect(request, 'start')
    end_str = expect(request, 'end')
    status = expect(request, 'status')
    try:
        cut_id = int(cut_id_str)
        start = int(start_str)
        end = int(end_str)
        assert status in EditStatus
    except:
        input_error()

    cut = db.session.query(Cut).get(cut_id)
    if not cut:
        input_error()

    cut.start = start
    cut.end = end
    cut.edit_status = status
    
    return {}

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static/', path)

if __name__ == '__main__':
    print("Please run using gunicorn main:app. Exiting.")
