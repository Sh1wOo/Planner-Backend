from pydantic_settings import BaseSettings, SettingsConfigDict

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

settings = Settings()
