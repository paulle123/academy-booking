FROM python:3.12-slim

WORKDIR /app

# Layer-caching: requirements change rarely, code changes often — copying
# requirements first means `docker build` reuses the pip layer on code edits.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as non-root (container security baseline). /data is where the
# persistent volume mounts in production.
RUN useradd -m appuser && mkdir -p /data && chown appuser /data
USER appuser
ENV DATABASE_PATH=/data/academy.db

# Init + seed are idempotent, so running them on every boot is safe;
# then hand off to gunicorn (a real WSGI server — Flask's dev server is
# single-threaded and not hardened).
CMD flask --app app init-db && flask --app app seed-db && \
    gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 "app:create_app()"
