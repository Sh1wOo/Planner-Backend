from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    refresh_token: Mapped[str | None] = mapped_column(String(512), nullable=True)

    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="owner", cascade="all, delete-orphan")
