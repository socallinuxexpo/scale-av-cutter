from app import db
from models import RoomDay, Talk

import iso8601
import json


def parse_signjson(data):
    talks = []

    for item in json.loads(data):
        if not item.get("StartTime") or not item.get("EndTime"):
            continue
        if "expo" in (item.get("Location") or "").lower():
            continue
        start_time = iso8601.parse_date(item["StartTime"])
        end_time = iso8601.parse_date(item["EndTime"])
        talk = {
            "room": item["Location"],
            "day": start_time.strftime("%A"),
            "path": item["Link"],
            "start": start_time,
            "end": end_time,
            "thumbnail": 0,
            "title": item["Name"],
            "speakers": item.get("Speakers") or "",
            "description": item.get("Description") or "",
        }
        talks.append(talk)

    return talks


def import_talks(talks, force_add):
    for talk in talks:
        # See if the RoomDay exists
        room_day = db.session.query(RoomDay)\
                        .filter(RoomDay.room == talk['room'])\
                        .filter(RoomDay.day == talk['day'])\
                        .first()
        if not room_day:
            room_day = RoomDay(
                room=talk['room'],
                day=talk['day'],
                date=talk['start'].date(),
                vid='',
            )
            db.session.add(room_day)
            db.session.flush()

        # Create talk data
        talk_data = Talk(
            room_day_id=room_day.id,
            path=talk['path'],
            speakers=talk['speakers'],
            sched_start=talk['start'].strftime("%H:%M"),
            sched_end=talk['end'].strftime("%H:%M"),
            title=talk['title'],
            description=talk['description'],
        )

        # See if the Talk already exists
        existing = db.session.query(Talk)\
                       .filter(Talk.path == talk['path'])\
                       .first()
        if not existing or force_add:
            db.session.add(talk_data)
        else:
            # If talk already exists, update its fields
            existing.room_day_id = talk_data.room_day_id
            existing.sched_start = talk_data.sched_start
            existing.sched_end = talk_data.sched_end
            existing.title = talk_data.title
            existing.description = talk_data.description
