from app import db
from models import RoomDay, Talk

from xml.etree.ElementTree import fromstring
from flask import Markup

import iso8601

def parse_signxml(data):
    talks = []

    # Collect all talks
    root = fromstring(data)
    for node in root:
        # Since the HTML inside Time are not actual valid XML, they have to be
        # re-parsed to become an element
        time_ele = fromstring(node.find("Time").text)
        start, end = time_ele.findall(".//span[@property='dc:date']")
        start_time = iso8601.parse_date(start.get("content"))
        end_time = iso8601.parse_date(end.get("content"))
        title = node.find("Title").text
        speakers = node.find("Speakers").text
        speakers = speakers if speakers is not None else ""
        description = Markup(node.find("Short-abstract").text).striptags()
        description = description if description is not None else ""
        path = node.find("Path").text
        room = node.find("Room").text
        day = Markup(node.find("Day").text).striptags()
        talk = {
            "room": room,
            "day": day,
            "path": path,
            "start": start_time,
            "end": end_time,
            "title": title,
            "speakers": speakers,
            "description": description,
        }
        talks.append(talk)

    return talks

def import_talks(talks):
    for talk in talks:
        # See if the RoomDay exists
        room_day = db.session.query(RoomDay)\
                        .filter(RoomDay.room == talk['room'])\
                        .filter(RoomDay.day == talk['day'])\
                        .first()
        if not room_day:
            room_day = RoomDay(
                room = talk['room'],
                day = talk['day'],
                date = talk['start'].date(),
                vid = '',
            )
            db.session.add(room_day)
            db.session.flush()

        # Create talk data
        talk_data = Talk(
            room_day_id = room_day.id,
            path = talk['path'],
            speakers = talk['speakers'],
            sched_start = talk['start'].strftime("%H:%M"),
            sched_end = talk['end'].strftime("%H:%M"),
            title = talk['title'],
            description = talk['description'],
        )
        
        # See if the Talk already exists
        talk = db.session.query(Talk)\
                    .filter(Talk.path == talk['path'])\
                    .first()
        if not talk:
            db.session.add(talk_data)
        else:
            # If talk already exists, we may need to update some of its fields
            talk.room_day_id = talk_data.room_day_id
            talk.sched_start = talk_data.sched_start
            talk.sched_end = talk_data.sched_end
            talk.title = talk_data.title
            talk.description = talk_data.description
