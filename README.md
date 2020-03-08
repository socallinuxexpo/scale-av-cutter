scale-av-cutter
===

Flask application to streamline process of splitting captured day-long
recordings into separate talks.

Note that if you only want to run the [tools][./tools], you won't need to
install the dependencies for this Flask app.


Requirements
---

I'm sorry, but you must use Python 3.6+. Recommended to use virtualenv to
install requirements.

```
pip install -r requirements.txt
```


Config
---

scale-av-cutter runs on environment variables. You must set these:

- `SECRET_KEY`: [See Flask doc](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)
- `ADMIN_KEY`: Group password for admin role
- `REVIEWER_KEY`: Group password for reviewer role
- `EDITOR_KEY`: Group password for editor role
- `DATABASE_URL`: [See SQLAlchemy doc](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
- `APP_SETTINGS`: What config module to use. Pick either `config.DevelopmentConfig` or `config.ProductionConfig`


Usage
---

Run scale-av-cutter somewhere, like Heroku, a cloud VM, or even your local
machine. Let's say you do the latter.

```
gunicorn main:app
```

You should then import all the talks of a year via the `/xml` endpoint, passing
it a URL to the year's signxml.

```
curl \
  localhost:8000/xml \
  -X POST \
  -d "url=<URL OF SIGNXML" \
  -b "password=<ADMIN_KEY>"
```

This is safe to call repeatedly. During a convention, if descriptions or
contents of certain talks update, reinvoking /xml should update it.

Now visit the index page, login as admin, and set the Youtube VID of each
room-day's stream. Let your editors go wild with inputting cut times. Let your
reviewers approve each cut.

After all the input is complete, grab the set of all Done and Approved cuts:

```
curl \
  http://localhost:5000/json?approved=1 \
  -b "password=<ADMIN_KEY" \
  > approved.json
```

This endpoint also accepts a "day" parameter to filter by Thursday, Friday,
etc.

Once you have this JSON file, you can check out the [tools][./tools] to
actually process the cuts.
