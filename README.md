# scale-av-cutter

Flask application to streamline process of splitting captured day-long
recordings into separate talks.

[!NOTE]
If you only want to run the [tools](./tools) for downloading,
cutting, and uploading videos, you can just install the dependencies described
in that directory, instead of the dependencies for this Flask app.


## Quick Start Guide

### Setup

Install the python dependencies:
```
pip install -r requirements.txt
```

Copy the sample environment file and edit it as needed:
```
cp .env.example .env
```

[!NOTE]
The SQLite database file will be created automatically on first run at the file specified in the environment file by `DATABASE_URL`


Run the app:
```
gunicorn main:app
```



## Dependencies

This app uses the `dotenv` package to load environment variables from a `.env` file.

This app uses SQLite as its database. No database server installation is required —
SQLite is built into Python.

I recommend using virtualenv to isolate the dependencies you'll need for this project.
Use either your package manager or pip to install virtualenv itself, create an
environment, and activate it. Then:

```
pip install -r requirements.txt
```


## Config

scale-av-cutter runs on environment variables, loaded from `.env`. You must set these:

- `SECRET_KEY`: [See Flask doc](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)
- `ADMIN_KEY`: Group password for admin role
- `REVIEWER_KEY`: Group password for reviewer role
- `EDITOR_KEY`: Group password for editor role
- `DATABASE_URL`: SQLite example: `sqlite:///scale_av_cutter.db`. [See SQLAlchemy doc](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
- `APP_SETTINGS`: What config module to use. Pick either `config.DevelopmentConfig` or `config.ProductionConfig`


## Usage

Run scale-av-cutter somewhere, like a cloud VM or your local machine (make sure you
have all of the required [environment variables](#config) set).

```
gunicorn main:app
```

By default, gunicorn binds to localhost, port 8000. To open it up to the world
at a specific port (e.g. 8000), run it as:

```
gunicorn -b 0.0.0.0:8000 main:app
```

You can then import all the talks of a year via the `/loadsigns` endpoint, passing it
a URL to the year's signs JSON data.

Example: [https://www.socallinuxexpo.org/scale/23x/signs](https://www.socallinuxexpo.org/scale/23x/signs)

```
curl \
  localhost:8000/loadsigns \
  -X POST \
  -d "url=<URL OF SIGNS JSON>" \
  -b "password=<ADMIN_KEY>"
```

This is safe to call repeatedly. During a convention, if descriptions or
contents of certain talks update, reinvoking `/loadsigns` should update it.

Now visit the index page, login as admin, and set the Youtube VID of each
room-day's stream. Let your editors go wild with inputting cut times. Let your
reviewers make the final tweaks or judgment of usability.

After all the input is complete, grab the set of all reviewed Done cuts:

```
curl \
  http://localhost:8000/json \
  -b "password=<ADMIN_KEY>" \
  > approved.json
```

Once you have this JSON file, you can check out the [tools](./tools) to
actually process the cuts.
