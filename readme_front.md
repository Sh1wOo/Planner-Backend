# Frontend / Mini App Integration for Planner

## Цель
Перед тем как пользователь будет редактировать задачи из мини-приложения, он должен быть авторизован. При первом открытии мини-приложения пользователь должен либо зарегистрироваться, либо войти, и мы должны сохранить его Telegram-профиль, чтобы привязать действия к реальному Telegram-пользователю.

## Что уже есть на backend

- Авторизация через API:
  - `POST /auth/register`
  - `POST /auth/login`
  - `POST /auth/refresh`
  - `POST /auth/logout`
  - `GET /auth/me`
- Авторизация выполняется через HTTP-only cookie: `access_token` и `refresh_token`.
- CORS разрешает только origin из `settings.frontend_url`.
- В Telegram-боте есть кнопка веб-приложения (`WEB_APP_TEXT`).

## Что нужно добавить на frontend

### 1. Проверка авторизации при загрузке Mini App

При открытии приложения из Telegram:
- выполнить `GET /auth/me`
- если ответ `200`, значит пользователь уже авторизован
- если ответ `401`, показать экран входа/регистрации

### 2. Экран регистрации/входа

Добавить форму:
- email
- username (только при регистрации)
- password

Вызовы API:
- `POST /auth/register`
- `POST /auth/login`

После успешного входа/регистрации backend автоматически ставит cookie, поэтому дальше фронтенд должен продолжить работу в авторизованном состоянии.

### 3. Сохранение Telegram-пользователя

Нужно добавить на backend endpoint для сохранения/связывания телеграм-пользователя с текущим авторизованным пользователем. Пример:
- `POST /auth/telegram` или `POST /auth/link-telegram`

Тело запроса должно содержать данные из Telegram WebApp, например:
- `telegram_id`
- `username`
- `first_name`
- `last_name`
- `init_data` (опционально, если нужна проверка данных Telegram)

Frontend должен вызвать этот endpoint после авторизации и получения данных Telegram из `window.Telegram.WebApp`.

### 4. Использование Telegram WebApp данных

При старте мини-приложения в клиенте нужно получить:
- `window.Telegram.WebApp.initData`
- `window.Telegram.WebApp.initDataUnsafe.user`

Эти данные нужно отправить на backend после успешного логина / регистрации.

### 5. Блокировка редактирования до авторизации

Перед любым действием, которое изменяет задачу, проверять, что пользователь авторизован. Если нет — редиректить на экран входа.

## Что нужно добавить на backend

### 1. Поле для Telegram-идентификации

В модель `User` желательно добавить поля:
- `telegram_id`
- `telegram_username`
- `telegram_first_name`
- `telegram_last_name`

Или отдельную таблицу `TelegramUser`, если нужна отдельная сущность.

### 2. Эндпоинт привязки Telegram

Добавить в `app/routers/auth.py` маршрут вида:
```python
@router.post("/telegram")
async def link_telegram(data: TelegramLinkRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    current_user.telegram_id = data.telegram_id
    current_user.telegram_username = data.username
    current_user.telegram_first_name = data.first_name
    current_user.telegram_last_name = data.last_name
    await db.commit()
    return current_user
```

### 3. Проверка origin / CORS

Убедиться, что `frontend_url` в `.env` совпадает с тем доменом, с которого открывается webapp. Telegram загружает веб-приложение по URL из `TELEGRAM_WEBAPP_URL`, и backend должен разрешать этот origin.

## Поток работы

1. Пользователь нажимает кнопку Mini App в Telegram.
2. Telegram открывает ваш фронтенд по `TELEGRAM_WEBAPP_URL`.
3. Фронтенд выполняет `GET /auth/me`.
4. Если пользователь не авторизован, показывается форма входа/регистрации.
5. После входа фронтенд отправляет Telegram-данные на backend для привязки.
6. После этого пользователь может работать с задачами.

## Важно

- Backend не авторизует пользователя сам через Telegram WebApp — нужна стандартная регистрация/вход.
- После регистрации/входа frontend должен сохранить статус авторизации только через cookie; токены не хранятся в localStorage.
- В текущем backend нет явного эндпоинта для сохранения telegram-пользователя, поэтому его нужно добавить.

## Резюме

На клиенте нужно:
- добавить проверку `GET /auth/me` при открытии mini app
- реализовать экран регистрации/входа
- отправлять данные Telegram-пользователя на новое API для привязки
- не позволять редактировать задачи до авторизации

На сервере нужно:
- добавить endpoint для связи Telegram-профиля с пользователем
- расширить модель пользователя / добавить таблицу для Telegram-профиля
- убедиться, что CORS и `frontend_url` корректно настроены
