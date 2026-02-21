import json
import os
import sys
import urllib.request
from unittest.mock import MagicMock

"""
This file tests the signjson.py file by loading the live schedule
from the SCALE site.

This test also prints out a neat report at the end showing the room usage
for each day.
"""

# Stub out Flask/SQLAlchemy imports so signjson can be imported
# without a running app or database connection.
sys.modules['app'] = MagicMock()
sys.modules['models'] = MagicMock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from signjson import parse_signjson

URL = "https://www.socallinuxexpo.org/scale/23x/signs"

print(f"Fetching {URL} ...")
with urllib.request.urlopen(URL) as response:
    data = response.read()

for item in json.loads(data):
    for key, value in item.items():
        if not value:
            print(f"  WARNING: empty field '{key}' in item: {item.get('Name') or item.get('Link') or '(unknown)'}")

talks = parse_signjson(data)

for talk in talks:
    print(f"  [{talk['day']}] {talk['start'].strftime('%H:%M')}–{talk['end'].strftime('%H:%M')}  {talk['room']}")
    print(f"    {talk['title']}")
    print(f"    Speakers: {talk['speakers']}")
    print(f"    Path:     {talk['path']}")
    print()

# Room report: group talks by day and room
from collections import defaultdict
by_day_room = defaultdict(list)
for talk in talks:
    by_day_room[(talk['day'], talk['room'])].append(talk)

days_ordered = sorted(set(t['day'] for t in talks), key=lambda d: talks[[t['day'] for t in talks].index(d)]['start'])
print("\n--- Room Report ---")
for day in days_ordered:
    print(f"\n{day}:")
    rooms = sorted(room for (d, room) in by_day_room if d == day)
    for room in rooms:
        room_talks = sorted(by_day_room[(day, room)], key=lambda t: t['start'])
        first, last = room_talks[0], room_talks[-1]
        print(f"  {room}")
        print(f"    Starts: {first['start'].strftime('%H:%M')}  {first['title']}")
        print(f"    Ends:   {last['end'].strftime('%H:%M')}  {last['title']}")

print(f"\nTotal talks loaded: {len(talks)}")