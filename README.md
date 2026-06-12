# Planner Backend

FastAPI + PostgreSQL (asyncpg) + Alembic

## Структура проекта

```
planner-backend/
├── .env
├── requirements.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
└── app/
    ├── main.py
    ├── config.py
    ├── database.py
    ├── dependencies.py
    ├── models/
    │   ├── user.py
    │   └── task.py
    ├── schemas/
    │   ├── auth.py
    │   └── task.py
    ├── services/
    │   └── auth.py
    └── routers/
        ├── auth.py
        └── tasks.py
```

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
uvicorn app.main:app --reload
```

Таблицы создаются автоматически при старте через `Base.metadata.create_all`.

## Миграции (Alembic)

```bash
# Первая миграция
alembic revision --autogenerate -m "initial"
alembic upgrade head

# После изменений модели
alembic revision --autogenerate -m "add column ..."
alembic upgrade head
```

## API Endpoints

### Auth
| Метод | URL             | Описание               |
|-------|-----------------|------------------------|
| POST  | /auth/register  | Регистрация            |
| POST  | /auth/login     | Вход                   |
| POST  | /auth/logout    | Выход                  |
| POST  | /auth/refresh   | Обновление токена      |
| GET   | /auth/me        | Текущий пользователь   |

### Tasks
| Метод  | URL             | Описание                                          |
|--------|-----------------|---------------------------------------------------|
| POST   | /tasks/         | Создать задачу                                    |
| GET    | /tasks/         | Список задач (фильтры: due_date, priority, completed) |
| GET    | /tasks/day      | Задачи на сегодня                                 |
| GET    | /tasks/{id}     | Одна задача                                       |
| PATCH  | /tasks/{id}     | Обновить задачу                                   |
| DELETE | /tasks/{id}     | Удалить задачу                                    |

### Приоритеты задач
- `low` — низкий
- `medium` — средний (по умолчанию)
- `high` — высокий

## Примеры запросов

### Регистрация
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"user1","password":"secret123"}'
```

### Создать задачу на дату с приоритетом
```bash
curl -c cookies.txt -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"Купить хлеб","due_date":"2026-06-10","priority":"high"}'
```

### Задачи на сегодня
```bash
curl -b cookies.txt http://127.0.0.1:8000/tasks/day
```

### Задачи за конкретный день
```bash
curl -b cookies.txt "http://127.0.0.1:8000/tasks/?due_date=2026-06-10"
```

### Обновить задачу
```bash
curl -b cookies.txt -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"completed":true,"priority":"low"}'
```

### Удалить задачу
```bash
curl -b cookies.txt -X DELETE http://127.0.0.1:8000/tasks/1
```

## Telegram-бот и Mini App
Для запуска Telegram-бота добавьте в `.env`:

```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
TELEGRAM_WEBAPP_URL=https://example.com/telegram-webapp
TELEGRAM_BOT_OWNER_ID=1  # числовой id пользователя в базе данных
```

> Важно: не устанавливайте пакет `telegram`. Используйте только `python-telegram-bot[asyncio]`.
> Если вы ранее устанавливали `telegram`, удалите его командой `pip uninstall telegram`.

Бот поддерживает команды:
- `/start` или `/help` — показать список команд и кнопку открытия мини-приложения
- `/tasks` — получить список задач для пользователя с `owner_id`, указанным в `TELEGRAM_BOT_OWNER_ID`
- `/add Заголовок | Описание | YYYY-MM-DD | priority` — создать задачу
- `/edit ID | Заголовок | Описание | YYYY-MM-DD | priority | completed` — обновить задачу

При отправке текста `открыть приложение` бот предлагает клавиатуру с кнопкой Mini App и под сообщением также выводит кнопку для открытия веб-приложения.
