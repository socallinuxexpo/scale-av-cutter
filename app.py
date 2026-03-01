from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from time import time
import os

load_dotenv()

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.jinja_env.globals['static_ts'] = int(time())

db = SQLAlchemy(app)

migrate = Migrate(app, db)
