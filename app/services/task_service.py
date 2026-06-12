from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task


async def get_tasks_for_user(session: AsyncSession, user_id: int) -> list[Task]:
    result = await session.execute(
        select(Task)
        .where(Task.owner_id == user_id)
        .order_by(Task.due_date.asc())
    )
    return result.scalars().all()
