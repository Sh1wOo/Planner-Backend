#!/bin/sh
set -e

echo "Starting entrypoint..."

# Run alembic migrations if database URL is provided
if [ -n "$ALEMBIC_DATABASE_URL" ]; then
  echo "Running alembic upgrade head"
  if ! alembic upgrade head; then
    echo "alembic upgrade failed"
    exit 1
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7878}
