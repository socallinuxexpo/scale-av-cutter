FROM python:3.10.6-slim

# Install PostgreSQL build dependencies (required for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Required environment variables (pass at runtime):
#   SECRET_KEY     - Flask secret key
#   ADMIN_KEY      - Admin role group password
#   REVIEWER_KEY   - Reviewer role group password
#   EDITOR_KEY     - Editor role group password
#   DATABASE_URL   - SQLAlchemy database URL (e.g. postgresql://user:pass@host/db)
#   APP_SETTINGS   - Config class (config.ProductionConfig or config.DevelopmentConfig)


EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app", "--log-file", "-"]
