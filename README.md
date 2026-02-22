# scale-av-cutter

Flask application to streamline process of splitting captured day-long
recordings into separate talks.

[!NOTE]
If you only want to run the [tools](./tools) for downloading,
cutting, and uploading videos, you can just install the dependencies described
in that directory, instead of the dependencies for this Flask app.


## Quick Start Guide

This is perfect for those just getting their feet wet and want to quickly run the app to test and/or develop this application. This guide assumes you have docker installed. If not, see the [Docker Install Guide](https://docs.docker.com/desktop/)

### Setup
Install the python dependencies:
```
pip install -r requirements.txt
```

Copy the sample environment file:
```
cp .env.example .env
```

Make whatever changes you want.

Start the database:

```
docker compose up db -d
```

This starts a Postgres database on localhost:5432 with user `scale` and sample password `scale`

Run the app:
```
gunicorn main:app
```

### Shutdown
To turn off the postgres DB:
```
docker compose down
```

To turn off the postgress DB and delete the DB's data:
```
docker compose down -v
```

## Dependencies

This app uses the `dotenv` package to automagically load environment variables from a `.env` file.

By default, this app assumes the use of PostgreSQL as the backing database, so
you must install a bunch of build tools as well Postgresql itself. If you only
want to run this **locally**, it's far easier to just use SQLite. You can
either edit `requirements.txt` and take out the `psycopg2` requirement, or just
filter it out when performing the pip install.

[!NOTE]
Running postgres locally has been made less scary now via docker compose. See the [Quick Start Guide](#quick-start-guide) above.

### Manually Setting Up PostgreSQL

This section is only for if you want to use PostgreSQL as the backing database, and set it up manually:

Install the following from your package manager.

CentOS-based:

```
sudo yum install postgresql postgresql-devel gcc python3-devel
```

Debian-based:

```
sudo apt install postgresql libpq-dev gcc python3-dev
```

Example of configuring postgresql in an Ubuntu system:

```
sudo su - postgres
psql
create user SOME_USER encrypted password 'SOME_PASSWORD';
create database scale_av_cutter_test;
grant all privileges on database scale_av_cutter_test to SOME_USER;
```

Then, you'll be able to use a SQLAlchemy string (`DATABASE_URL`) of `postgres://SOME_USER:SOME_PASSWORD@localhost/scale_av_cutter_test`.

### Python dependencies

I recommend using virtualenv to manage isolate the dependencies you'll need for
this project. Use either your package manager or pip to install virtualenv
itself, create an environment, and activate it.

Then:

```
pip install -r requirements.txt
```

If you see an error with building wheel for psycopg2, you will need to follow
the [PostgreSQL dependencies](#postgresql-dependencies) section first. If the
error persists, file an issue.


## Config

scale-av-cutter runs on environment variables. You must set these:

- `SECRET_KEY`: [See Flask doc](https://flask.palletsprojects.com/en/1.1.x/config/#SECRET_KEY)
- `ADMIN_KEY`: Group password for admin role
- `REVIEWER_KEY`: Group password for reviewer role
- `EDITOR_KEY`: Group password for editor role
- `DATABASE_URL`: [See SQLAlchemy doc](https://docs.sqlalchemy.org/en/13/core/engines.html#database-urls)
- `APP_SETTINGS`: What config module to use. Pick either `config.DevelopmentConfig` or `config.ProductionConfig`


## Usage


Run scale-av-cutter somewhere, like Heroku, a cloud VM, or even your local
machine. Let's say you do the latter (make sure you have all of the required [environment variables](#config) set).

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
  -d "url=<URL OF SIGNXML>" \
  -b "password=<ADMIN_KEY>"
```

This is safe to call repeatedly. During a convention, if descriptions or
contents of certain talks update, reinvoking /xml should update it.

Now visit the index page, login as admin, and set the Youtube VID of each
room-day's stream. Let your editors go wild with inputting cut times. Let your
reviewers make the final tweaks or judgment of usability.

After all the input is complete, grab the set of all reviewed Done cuts:

```
curl \
  http://localhost:5000/json \
  -b "password=<ADMIN_KEY>" \
  > approved.json
```

Once you have this JSON file, you can check out the [tools](./tools) to
actually process the cuts.
