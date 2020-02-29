from app import db
from models import RoomDay, Cut

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
        speaker = node.find("Speakers").text
        description = Markup(node.find("Short-abstract").text).striptags()
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
            "speaker": speaker,
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
                vid = None
            )
            db.session.add(room_day)
            db.session.flush()

        # Create cut data
        cut_data = Cut(
            room_day_id = room_day.id,
            path = talk['path'],
            sched_start = talk['start'].strftime("%H:%M"),
            sched_end = talk['end'].strftime("%H:%M"),
            title = talk['title'],
            description = talk['description'],
        )
        
        # See if the Cut already exists
        cut = db.session.query(Cut)\
                    .filter(Cut.path == talk['path'])\
                    .first()
        if not cut:
            db.session.add(cut_data)
        else:
            # If cut already exists, we may need to update some of its fields
            cut.room_day_id = cut_data.room_day_id
            cut.sched_start = cut_data.sched_start
            cut.sched_end = cut_data.sched_end
            cut.title = cut_data.title
            cut.description = cut_data.description
