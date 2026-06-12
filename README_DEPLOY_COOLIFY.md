Как задеплоить проект на Coolify

Короткая инструкция и необходимые файлы уже добавлены (Dockerfile, entrypoint.sh, .dockerignore).

Шаги для деплоя в Coolify:

1. В репозитории должны быть `Dockerfile` в корне — уже есть.
2. Войдите в Coolify и создайте новое приложение, выбрав деплой из репозитория (GitHub/GitLab).
3. В настройках приложения укажите путь к Dockerfile (по умолчанию `Dockerfile`).
4. В разделе переменных окружения в Coolify добавьте только те переменные, которые вы хотите переопределить. По умолчанию проект использует локальный SQLite:
   - `DATABASE_URL` (необязательно) — `sqlite+aiosqlite:///./dev.db` или любая другая async база
   - `ALEMBIC_DATABASE_URL` (необязательно) — `sqlite:///./dev.db`
   - `SECRET_KEY` (необязательно)
   - `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
   - `FRONTEND_URL`
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBAPP_URL`, `TELEGRAM_BOT_OWNER_ID` (если нужен Telegram бот)
   - `PORT` (опционально, Coolify задаёт порт автоматически; приложение слушает `${PORT:-7878}`)
5. (Опционально) В разделе Build/Deploy команд можно настроить дополнительную команду перед запуском, но контейнер уже выполняет `alembic upgrade head` в `entrypoint.sh`.

Локально для теста:

```
docker compose build
docker compose up
```

Если хотите, могу:
- настроить автоматические миграции через отдельный сервис в `docker-compose.yml`;
- добавить Healthcheck в `Dockerfile`/Compose;
- или подготовить .github/workflows для CI/CD (GitHub Actions) и авто-деплоя в Coolify.
