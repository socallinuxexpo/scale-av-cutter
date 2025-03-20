from app import app, db

from models import *
import argparse
import os

app.app_context().push()

def parse_args():
    parser = argparse.ArgumentParser(description="Delete all talk entries in the database not corresponding to specified SCALE year number, ex. 22.")

    parser.add_argument("database", help="Path to database file")
    parser.add_argument("scale_num", type=int, help="SCALE number, ex. If targetting 2025 SCALE, which was 22x, then input 22")
    return parser.parse_args()

def main():
    args = parse_args()

    print(f"Deleting {args.database} entries not from SCALE {args.scale_num}x")
    if not os.path.isfile(args.database):
        print("Error: Database file not found.")
        return
    
    # Delete all talks not from specified SCALE year, prevent deleting all talks
    scale_num_path = "/scale/" + str(args.scale_num) + "x/presentations/"
    talks = db.session.query(Talk)\
                .filter(~Talk.path.contains(scale_num_path))
    total_talks = db.session.query(Talk).count()

    if talks.count() == total_talks:
        print("Recheck the SCALE year number inputted. Current input will delete all talks from database.")
        return
    else:
        talks.delete()

    # Delete roomdays that no longer have any talks in them
    empty_roomdays = db.session.query(RoomDay)\
                .outerjoin(Talk).filter(Talk.room_day_id.is_(None))
    
    for roomday in empty_roomdays:
        db.session.delete(roomday)
    
    db.session.commit()

if __name__ == "__main__":
    main()