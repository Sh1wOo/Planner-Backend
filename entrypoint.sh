#!/bin/sh
set -e

echo "Starting entrypoint..."

# Run alembic migrations (safe for SQLite); fail container if migration fails
echo "Running alembic upgrade head"
if ! alembic upgrade head; then
  echo "alembic upgrade failed"
  exit 1
fi

echo "Starting uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7878}
