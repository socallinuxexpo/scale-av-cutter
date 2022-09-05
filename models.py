from app import db

class StringEnum:

    @classmethod
    def values(cls):
        attrs = cls.__dict__.keys()
        return set(attr for attr in attrs if not attr.startswith("__") and attr != "values")

class EditStatus(StringEnum):
    incomplete = 'incomplete'
    done = 'done'
    unusable = 'unusable'

class ReviewStatus(StringEnum):
    reviewing = 'reviewing'
    done = 'done'
    unusable = 'unusable'

class RoomDay(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    room        = db.Column(db.Text, nullable=False)
    day         = db.Column(db.Text, nullable=False)
    date        = db.Column(db.Date, nullable=False)
    vid         = db.Column(db.Text, nullable=False)
    comment     = db.Column(db.Text, nullable=False, default="")

    checked_out_by = db.Column(db.Text, nullable=False, default="")

    talks = db.relationship('Talk', order_by="Talk.sched_start")

db.Index('room_day_index', RoomDay.room, RoomDay.day)

class Talk(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    room_day_id = db.Column(db.Integer, db.ForeignKey('room_day.id'))
    path        = db.Column(db.Text, nullable=False, index=True)
    speakers    = db.Column(db.Text, nullable=False)
    sched_start = db.Column(db.Text, nullable=False)
    sched_end   = db.Column(db.Text, nullable=False)
    title       = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    notes       = db.Column(db.Text, nullable=False, default="")

    start       = db.Column(db.Integer, default=0, nullable=False)
    end         = db.Column(db.Integer, default=0, nullable=False)

    review_status   = db.Column(db.VARCHAR, default=ReviewStatus.reviewing, nullable=False)
    edit_status     = db.Column(db.VARCHAR, default=EditStatus.incomplete, nullable=False)

    last_edited_by = db.Column(db.Text, nullable=False, default="")
