import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@dataclass
class TelegramMiniAppUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None


def validate_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> TelegramMiniAppUser:
    if not init_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="init_data is required")

    pairs = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = pairs.pop("hash", None)

    if not received_hash:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Telegram hash")

    auth_date = pairs.get("auth_date")
    if not auth_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing auth_date")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram init data")

    user_raw = pairs.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Telegram user not found in init_data")

    try:
        user_data: dict[str, Any] = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Telegram user payload")

    return TelegramMiniAppUser(
        id=int(user_data["id"]),
        username=user_data.get("username"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
    )


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def link_telegram_to_user(
    session: AsyncSession,
    current_user: User,
    init_data: str,
    bot_token: str,
) -> User:
    tg_user = validate_telegram_init_data(init_data=init_data, bot_token=bot_token)

    existing_user = await get_user_by_telegram_id(session, tg_user.id)
    if existing_user and existing_user.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This Telegram account is already linked to another user",
        )

    current_user.telegram_id = tg_user.id
    current_user.telegram_username = tg_user.username
    current_user.telegram_first_name = tg_user.first_name

    await session.commit()
    await session.refresh(current_user)
    return current_user