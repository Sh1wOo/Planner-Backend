import asyncio
from datetime import datetime
from typing import Optional

try:
    from telegram import (
        InlineKeyboardButton,
        InlineKeyboardMarkup,
        KeyboardButton,
        ReplyKeyboardMarkup,
        Update,
        WebAppInfo,
    )
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
except ImportError as exc:
    raise ImportError(
        "python-telegram-bot[asyncio] is required for Telegram bot support. "
        "Uninstall any conflicting 'telegram' package and install via: pip install python-telegram-bot[asyncio]"
    ) from exc

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.task import Priority, Task

WEB_APP_TEXT = "Открыть приложение"


def build_web_app_button_text() -> str:
    return WEB_APP_TEXT


def build_web_app_reply_markup() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text=WEB_APP_TEXT, web_app=WebAppInfo(url=settings.telegram_webapp_url))
    return ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=False)


def build_web_app_inline_markup() -> InlineKeyboardMarkup:
    button = InlineKeyboardButton(text=WEB_APP_TEXT, web_app=WebAppInfo(url=settings.telegram_webapp_url))
    return InlineKeyboardMarkup([[button]])


def format_task(task: Task) -> str:
    status = "✅ выполнено" if task.completed else "❌ в работе"
    description = f"\n    {task.description}" if task.description else ""
    return (
        f"#{task.id} {task.title}\n"
        f"    Дата: {task.due_date.isoformat()}, приоритет: {task.priority.value}, {status}"
        f"{description}"
    )


async def fetch_tasks() -> list[Task]:
    async with AsyncSessionLocal() as db:
        query = select(Task).where(Task.owner_id == settings.telegram_bot_owner_id).order_by(Task.due_date.asc())
        result = await db.execute(query)
        return result.scalars().all()


async def create_task_from_text(title: str, description: Optional[str], due_date: str, priority: str) -> Task:
    try:
        due = datetime.fromisoformat(due_date).date()
    except ValueError:
        raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD.")

    try:
        priority_value = Priority(priority.lower()) if priority else Priority.medium
    except ValueError:
        raise ValueError("Приоритет должен быть low, medium или high.")

    async with AsyncSessionLocal() as db:
        task = Task(
            title=title,
            description=description,
            due_date=due,
            priority=priority_value,
            owner_id=settings.telegram_bot_owner_id,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task


async def update_task_from_text(task_id: int, title: Optional[str], description: Optional[str], due_date: Optional[str], priority: Optional[str], completed: Optional[str]) -> Task:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, task_id)
        if not task or task.owner_id != settings.telegram_bot_owner_id:
            raise LookupError("Задача не найдена")

        if title:
            task.title = title
        if description is not None:
            task.description = description
        if due_date:
            try:
                task.due_date = datetime.fromisoformat(due_date).date()
            except ValueError:
                raise ValueError("Неверный формат даты. Используйте YYYY-MM-DD.")
        if priority:
            try:
                task.priority = Priority(priority.lower())
            except ValueError:
                raise ValueError("Приоритет должен быть low, medium или high.")
        if completed is not None:
            task.completed = completed.lower().strip() in {"1", "true", "yes", "да", "y"}

        await db.commit()
        await db.refresh(task)
        return task


async def send_commands_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Я могу показать задачи, создать новую задачу или обновить существующую.\n\n"
        "Команды:\n"
        "/tasks — список задач\n"
        "/add Заголовок | Описание | YYYY-MM-DD | priority\n"
        "/edit ID | Заголовок | Описание | YYYY-MM-DD | priority | completed\n"
        "Отправьте текст \"открыть приложение\" или нажмите кнопку, чтобы открыть мини-приложение."
    )
    await update.message.reply_text(text, reply_markup=build_web_app_inline_markup())
    await update.message.reply_text("Нажмите кнопку ниже, чтобы открыть веб-приложение:", reply_markup=build_web_app_reply_markup())


async def ensure_authorized(update: Update) -> bool:
    """Return True if the Telegram user is the configured owner; otherwise send a help message and return False."""
    user = update.effective_user
    if not user or user.id != settings.telegram_bot_owner_id:
        # Prompt the user to open the web app to authenticate
        await update.message.reply_text(
            "Сначала надо авторизоваться в приложении",
            reply_markup=build_web_app_reply_markup(),
        )
        return False
    return True


async def list_tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_authorized(update):
        return

    tasks = await fetch_tasks()
    if not tasks:
        await update.message.reply_text("Сейчас задач нет. Создайте первую задачу командой /add.")
        return
    lines = [format_task(task) for task in tasks]
    await update.message.reply_text("Список задач:\n\n" + "\n\n".join(lines))


def parse_add_payload(text: str) -> tuple[str, Optional[str], str, str]:
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 2:
        raise ValueError("Используйте формат: /add Заголовок | Описание | YYYY-MM-DD | priority")

    title = parts[0]
    if len(parts) == 2:
        description = None
        due_date = parts[1]
        priority = "medium"
    else:
        description = parts[1] or None
        due_date = parts[2]
        priority = parts[3] if len(parts) >= 4 else "medium"
    return title, description, due_date, priority


async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payload = update.message.text.partition(" ")[2].strip()
    if not await ensure_authorized(update):
        return
    if not payload:
        await update.message.reply_text("Используйте формат: /add Заголовок | Описание | YYYY-MM-DD | priority")
        return

    try:
        title, description, due_date, priority = parse_add_payload(payload)
        task = await create_task_from_text(title, description, due_date, priority)
        await update.message.reply_text(f"Задача создана: #{task.id} {task.title}")
    except ValueError as exc:
        await update.message.reply_text(str(exc))


def parse_edit_payload(text: str) -> tuple[int, Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 2 or not parts[0].isdigit():
        raise ValueError("Используйте формат: /edit ID | Заголовок | Описание | YYYY-MM-DD | priority | completed")

    task_id = int(parts[0])
    title = parts[1] if parts[1] else None
    description = parts[2] if len(parts) >= 3 else None
    due_date = parts[3] if len(parts) >= 4 and parts[3] else None
    priority = parts[4] if len(parts) >= 5 and parts[4] else None
    completed = parts[5] if len(parts) >= 6 and parts[5] else None
    return task_id, title, description, due_date, priority, completed


async def edit_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    payload = update.message.text.partition(" ")[2].strip()
    if not await ensure_authorized(update):
        return
    if not payload:
        await update.message.reply_text("Используйте формат: /edit ID | Заголовок | Описание | YYYY-MM-DD | priority | completed")
        return

    try:
        task_id, title, description, due_date, priority, completed = parse_edit_payload(payload)
        task = await update_task_from_text(task_id, title, description, due_date, priority, completed)
        await update.message.reply_text(f"Задача обновлена: #{task.id} {task.title}")
    except ValueError as exc:
        await update.message.reply_text(str(exc))
    except LookupError:
        await update.message.reply_text("Задача не найдена или доступ запрещен.")


async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip().lower()
    if text == WEB_APP_TEXT.lower():
        await send_commands_message(update, context)
    elif text == "список задач":
        await list_tasks_command(update, context)


async def start_telegram_bot(app) -> None:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler(["start", "help"], send_commands_message))
    application.add_handler(CommandHandler("tasks", list_tasks_command))
    application.add_handler(CommandHandler("add", add_task_command))
    application.add_handler(CommandHandler("edit", edit_task_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    app.state.telegram_application = application
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await application.updater.wait_until_idle()


if __name__ == "__main__":
    print("Telegram bot module is not intended to be executed directly.")
