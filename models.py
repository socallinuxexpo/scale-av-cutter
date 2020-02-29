from app import db

EditStatus = ["incomplete", "done", "unusable"]
ReviewStatus = ["reviewing", "approved", "rejected"]

class RoomDay(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    room        = db.Column(db.Text, nullable=False)
    day         = db.Column(db.Text, nullable=False)
    vid         = db.Column(db.Text)

db.Index('room_day_index', RoomDay.room, RoomDay.day)

class Cut(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    room_day_id = db.Column(db.Integer, db.ForeignKey('room_day.id'))
    path        = db.Column(db.Text, nullable=False, index=True)
    sched_start = db.Column(db.Text, nullable=False)
    sched_end   = db.Column(db.Text, nullable=False)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)

    start       = db.Column(db.Integer, default=0, nullable=False)
    end         = db.Column(db.Integer, default=0, nullable=False)

    review_status   = db.Column(db.Enum(*ReviewStatus), default=ReviewStatus[0], nullable=False)
    edit_status     = db.Column(db.Enum(*EditStatus), default=EditStatus[0], nullable=False)

    room_day = db.relationship('RoomDay', backref='cuts')
