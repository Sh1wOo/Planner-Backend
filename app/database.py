from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import asyncio
import logging
from sqlalchemy import text


class Base(DeclarativeBase):
    pass


def normalize_async_database_url(url: str) -> str:
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

async_database_url = normalize_async_database_url(settings.database_url)
if async_database_url != settings.database_url:
    logging.getLogger("uvicorn.error").warning(
        "DATABASE_URL uses sync psycopg2 driver, switching to asyncpg for app runtime."
    )

engine = create_async_engine(
    async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=5,
    connect_args={"timeout": 5},
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def ensure_engine():
    """Ensure current engine is reachable; if not, switch to local SQLite for development.

    Returns True if fallback to SQLite was performed, False otherwise.
    """
    global engine, AsyncSessionLocal
    log = logging.getLogger("uvicorn.error")
    try:
        # quick connectivity check with short timeout
        async def _check():
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_check(), timeout=3)
        return False
    except Exception as exc:
        log.warning("Primary DB unreachable, switching to SQLite fallback: %s", exc)
        # create local sqlite engine
        fallback_url = "sqlite+aiosqlite:///./dev.db"
        try:
            engine = create_async_engine(fallback_url, echo=False)
            AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            return True
        except ModuleNotFoundError as mnf:
            log.error("aiosqlite is not installed, cannot use SQLite fallback: %s", mnf)
            return False
