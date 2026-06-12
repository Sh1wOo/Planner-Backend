from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.task import Task, Priority
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        priority=data.priority,
        owner_id=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    due_date: Optional[date] = Query(default=None, description="Фильтр по дате (YYYY-MM-DD)"),
    priority: Optional[Priority] = Query(default=None, description="Фильтр по приоритету"),
    completed: Optional[bool] = Query(default=None, description="Фильтр по статусу"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Task).where(Task.owner_id == current_user.id)
    if due_date is not None:
        query = query.where(Task.due_date == due_date)
    if priority is not None:
        query = query.where(Task.priority == priority)
    if completed is not None:
        query = query.where(Task.completed == completed)
    query = query.order_by(Task.due_date.asc(), Task.priority.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/day", response_model=list[TaskResponse])
async def get_tasks_for_today(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Задачи на сегодняшний день."""
    today = date.today()
    query = (
        select(Task)
        .where(Task.owner_id == current_user.id, Task.due_date == today)
        .order_by(Task.priority.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = await db.get(Task, task_id)
    if not task or task.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
