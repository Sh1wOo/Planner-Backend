from pydantic import BaseModel, EmailStr
from pydantic import BaseModel

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str

    model_config = {"from_attributes": True}

class TelegramLinkRequest(BaseModel):
    init_data: str

class TelegramLinkResponse(BaseModel):
    ok: bool
    telegram_id: int
    telegram_username: str | None = None
    telegram_first_name: str | None = None