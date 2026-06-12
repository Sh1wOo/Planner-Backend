import enum
from sqlalchemy import Integer, String, Text, Date, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum"), default=Priority.medium, nullable=False
    )
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="tasks")
