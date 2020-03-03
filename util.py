import flask
from functools import wraps

from app import db

class ScaleAVCutterError(Exception):
    def __init__(self, msg, *args):
        super(ScaleAVCutterError, self).__init__(*args)
        self.msg = msg

    def __repr__(self):
        return self.msg

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
    raise ScaleAVCutterError(msg)

def access_error():
    error('Insufficient access level')

def input_error():
    error('Input error')

def expect(request, arg, optional=False):
    if arg not in request.values:
        if not optional:
            input_error()
        else:
            return None
    return request.values[arg]
