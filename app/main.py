from contextlib import asynccontextmanager, suppress
import asyncio

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings
import app.database as database
from app.database import Base, ensure_engine

# Импорт моделей до create_all — обязательно
from app.models import user, task  # noqa: F401
from app.telegram_bot import start_telegram_bot

from app.routers import auth, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optionally skip DB initialization (useful when DB is unreachable in dev)
    if getattr(settings, "skip_db_init", False):
        import logging

        logging.getLogger("uvicorn.error").info("Skipping DB initialization because SKIP_DB_INIT is set")
        bot_task = None
        if settings.telegram_bot_token and settings.telegram_webapp_url:
            bot_task = asyncio.create_task(start_telegram_bot(app))
        try:
            yield
        finally:
            if bot_task:
                if hasattr(app.state, "telegram_application"):
                    await app.state.telegram_application.stop()
                bot_task.cancel()
                with suppress(asyncio.CancelledError):
                    await bot_task
        return

    bot_task = None
    try:
        # Ensure engine is reachable or switched to fallback before creating tables
        await ensure_engine()
        async with database.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        if settings.telegram_bot_token and settings.telegram_webapp_url:
            bot_task = asyncio.create_task(start_telegram_bot(app))
    except Exception as exc:  # don't let DB problems crash the whole app
        import logging

        logging.getLogger("uvicorn.error").exception("Database initialization failed: %s", exc)
    try:
        yield
    finally:
        if bot_task:
            if hasattr(app.state, "telegram_application"):
                await app.state.telegram_application.stop()
            bot_task.cancel()
            with suppress(asyncio.CancelledError):
                await bot_task


app = FastAPI(
    title="Planner API",
    description="Авторизация + задачи с приоритетами",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        {"detail": exc.errors()},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        {"detail": "Database unavailable. Please try again later."},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        {"detail": "Internal server error."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Planner API is running"}


@app.get("/health", tags=["Health"])
async def health():
    import asyncio
    import logging

    log = logging.getLogger("uvicorn.error")
    try:
        # ensure engine selected (may switch to fallback)
        fallback = await ensure_engine()
        from sqlalchemy import text

        async def _check():
            async with database.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_check(), timeout=2)
        return {"status": "ok", "db_fallback": fallback}
    except Exception as exc:
        log.debug("Health DB check failed: %s", exc)
        return {"status": "degraded", "db_fallback": False, "detail": str(exc)}
