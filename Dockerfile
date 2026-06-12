FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential libpq-dev gcc git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# copy project
COPY . /app/

# run as non-root
RUN adduser --disabled-password --gecos "" appuser || true
USER appuser

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]
