import flask
from functools import wraps

from app import db

class ScaleAVSplitterError(Exception):
    def __init__(self, msg, *args):
        super(ScaleAVSplitterError, self).__init__(*args)
        self.msg = msg

    def __repr__(self):
        return self.msg

def jsonify(inner):
    @wraps(inner)
    def wrapper(*args, **kwargs):
        return flask.jsonify(inner(*args, **kwargs))
    return wrapper

def catch_error(inner):
    @wraps(inner)
    def wrapper(*args, **kwargs):
        try:
            return inner(*args, **kwargs)
        except Exception as e:
            return {'error': repr(e)}
    return wrapper

def commit_db(inner):
    @wraps(inner)
    def wrapper(*args, **kwargs):
        try:
            res = inner(*args, **kwargs)
            db.session.commit()
            return res
        except Exception as e:
            db.session.rollback()
            raise e
    return wrapper

def error(msg):
    raise ScaleAVSplitterError(msg)

def admin_error():
    error('Incorrect admin credentials')

def input_error():
    error('Input error')

def expect(request, arg, optional=False):
    if arg not in request.values:
        if not optional:
            input_error()
        else:
            return None
    return request.values[arg]
