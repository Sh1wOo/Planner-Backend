from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./dev.db"
    alembic_database_url: str = "sqlite:///./dev.db"
    secret_key: str = "secret"
    skip_db_init: bool = False
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    frontend_url: str = "http://localhost:5173"
    telegram_bot_token: str | None = None
    telegram_webapp_url: str | None = None
    telegram_bot_owner_id: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Allow overriding only the secret via env, database URLs default to local SQLite.
secret = os.getenv("SECRET_KEY") or os.getenv("secret_key")

try:
    settings = Settings(secret_key=secret) if secret is not None else Settings()
except ValidationError as exc:
    log = logging.getLogger("uvicorn.error")
    missing = []
    for err in exc.errors():
        if err.get("type") == "missing":
            loc = err.get("loc") or []
            if loc:
                missing.append(loc[0])
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
    log.exception("Settings validation failed: %s", exc)
    raise
