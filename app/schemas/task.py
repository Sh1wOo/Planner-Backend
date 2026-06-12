from datetime import date
from typing import Optional
from pydantic import BaseModel, Field
from app.models.task import Priority


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: date
    priority: Priority = Priority.medium


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[Priority] = None
    completed: Optional[bool] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    due_date: date
    priority: Priority
    completed: bool
    owner_id: int

    model_config = {"from_attributes": True}
