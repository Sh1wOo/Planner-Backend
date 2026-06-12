from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import ValidationError
import logging
import os

class Settings(BaseSettings):
    database_url: str
    alembic_database_url: str
    secret_key: str
    skip_db_init: bool = False
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    frontend_url: str = "http://localhost:5173"
    telegram_bot_token: str | None = None
    telegram_webapp_url: str | None = None
    telegram_bot_owner_id: int = 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Normalize common uppercase env names into lowercase keys expected by Settings
for key in ("DATABASE_URL", "ALEMBIC_DATABASE_URL", "SECRET_KEY"):
    if os.getenv(key) and not os.getenv(key.lower()):
        os.environ[key.lower()] = os.getenv(key)

# Prepare init kwargs from available env vars (support both upper and lower case names)
init_kwargs = {}
for field in ("database_url", "alembic_database_url", "secret_key"):
    val = os.getenv(field) or os.getenv(field.upper())
    if val is not None:
        init_kwargs[field] = val

try:
    settings = Settings(**init_kwargs)
except ValidationError as exc:
    log = logging.getLogger("uvicorn.error")
    # collect missing fields for clearer error
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
