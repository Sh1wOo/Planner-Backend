from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse
from app.services.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, get_user_by_email, get_user_by_id,
)
from app.models.user import User
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])


def set_auth_cookies(response: Response, user_id: int) -> str:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 3600,
        path="/auth/refresh",
    )
    return refresh_token


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()

    refresh_token = set_auth_cookies(response, user.id)
    user.refresh_token = refresh_token
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already registered")
    await db.refresh(user)
    return user


@router.post("/login", response_model=UserResponse)
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    refresh_token = set_auth_cookies(response, user.id)
    user.refresh_token = refresh_token
    await db.commit()
    return user


@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user = await get_user_by_id(db, int(payload["sub"]))
    if not user or user.refresh_token != refresh_token:
        raise HTTPException(status_code=401, detail="Token revoked")

    new_refresh = set_auth_cookies(response, user.id)
    user.refresh_token = new_refresh
    await db.commit()
    return user


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.refresh_token = None
    await db.commit()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token", path="/auth/refresh")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
