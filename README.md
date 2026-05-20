# Events Provider API

API для управления мероприятиями и регистрацией билетов с поддержкой синхронизации с внешним провайдером событий.

## Возможности

- Синхронизация событий и мест с внешним Events Provider API
- Регистрация на мероприятия (покупка билетов)
- Отмена регистрации
- Transactional Outbox для гарантированной доставки уведомлений
- Интеграция с Capashino для отправки уведомлений
- Идемпотентность операций регистрации
- Мониторинг ошибок через GlitchTip

## Технологический стек

- **Python 3.13+**
- **FastAPI** - веб-фреймворк
- **SQLAlchemy 2.0** - ORM с async поддержкой
- **PostgreSQL** - база данных
- **Alembic** - миграции БД
- **httpx** - HTTP клиент
- **structlog** - структурированное логирование
- **sentry-sdk** - интеграция с GlitchTip
- **uv** - управление зависимостями
- **ruff** - линтер и форматтер

## Установка и запуск

### Требования

- Python 3.13+
- PostgreSQL 14+
- uv (установка: `pip install uv`)

### Локальная разработка

1. Клонировать репозиторий:
```bash
git clone <repository-url>
cd events-provider-api
```

2. Создать виртуальное окружение и установить зависимости:
```bash
uv venv
uv pip install -r requirements.txt
```

3. Создать файл `.env` на основе примера:
```bash
cp .env.example .env
```

4. Настроить переменные окружения в `.env`:
```env
# Database
POSTGRES_DATABASE_NAME=events_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USERNAME=postgres
POSTGRES_PASSWORD=admin

# Events Provider API
EVENTS_PROVIDER_API_URL=https://api.events-provider.com
X_API_KEY=your-api-key

# Capashino Notification Service
CAPASHINO_BASE_URL=https://capashino.dev-2.python-labs.ru
CAPASHINO_API_KEY=your-capashino-api-key

# Outbox Worker
OUTBOX_WORKER_INTERVAL=10
OUTBOX_MAX_ATTEMPTS=5

# GlitchTip (опционально)
SENTRY_DSN=https://your-glitchtip-dsn
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=1.0
```

5. Запустить PostgreSQL через Docker:
```bash
docker-compose up -d db
```

6. Применить миграции:
```bash
uv run alembic upgrade head
```

7. Запустить приложение:
```bash
uv run uvicorn app.main:app --reload --port 8000
```

API будет доступно по адресу: http://localhost:8000

Документация API (Swagger): http://localhost:8000/docs

## Архитектура

### Transactional Outbox Pattern

Для гарантированной доставки уведомлений используется паттерн Transactional Outbox:

1. При создании билета в той же транзакции сохраняется запись в таблицу `outbox`
2. Отдельный воркер периодически читает неотправленные записи
3. Воркер вызывает Capashino API для отправки уведомления
4. После успешной отправки запись помечается как отправленная

**Преимущества:**
- Гарантия доставки: событие не теряется при падении процесса
- Атомарность: либо сохраняются и билет, и событие, либо откатываются оба
- Retry логика: при временной недоступности Capashino повторные попытки

### Идемпотентность

POST `/api/tickets` поддерживает идемпотентность через опциональное поле `idempotency_key`:

- При первом запросе с ключом создается билет и сохраняется связь ключ → ticket_id
- При повторном запросе с тем же ключом возвращается существующий билет (201)
- При конфликте (тот же ключ, другие данные) возвращается 409 Conflict
- Ключ не сохраняется, если регистрация в Events Provider не удалась

### Интеграция с Capashino

Capashino - сервис уведомлений. После успешной покупки билета:

1. Запись создается в outbox
2. Воркер отправляет уведомление через POST `/api/notifications`
3. Используется idempotency_key для предотвращения дубликатов
4. При 4xx ошибках (кроме 409) запись помечается как failed
5. При 5xx или сетевых ошибках выполняются повторные попытки

### Мониторинг с GlitchTip

GlitchTip (совместим с Sentry SDK) автоматически отслеживает:
- Необработанные исключения в обработчиках запросов
- Ошибки в фоновых задачах
- Performance traces (при включенном traces_sample_rate)

## API Endpoints

### Синхронизация

- `POST /api/sync` - Запустить синхронизацию событий и мест

### События

- `GET /api/events` - Получить список событий
- `GET /api/events/{event_id}` - Получить событие по ID

### Билеты

- `POST /api/tickets` - Зарегистрироваться на мероприятие (купить билет)
  - Поддерживает `idempotency_key` для предотвращения дубликатов
- `DELETE /api/tickets/{ticket_id}` - Отменить регистрацию

### Здоровье

- `GET /api/health` - Проверка работоспособности сервиса

## Разработка

### Линтинг и форматирование

Проект использует ruff для линтинга и форматирования:

```bash
# Проверка
uv run ruff check .

# Автоисправление
uv run ruff check --fix .

# Форматирование
uv run ruff format .
```

### Pre-commit hooks

Настроены pre-commit хуки для автоматической проверки перед коммитом:

```bash
# Установка хуков
uv run pre-commit install

# Ручной запуск
uv run pre-commit run --all-files
```

### Миграции БД

Создание новой миграции:
```bash
uv run alembic revision -m "description"
```

Применение миграций:
```bash
uv run alembic upgrade head
```

Откат миграции:
```bash
uv run alembic downgrade -1
```

### Тестирование

```bash
uv run pytest
```

## CI/CD

Проект использует GitHub Actions для:
- Проверки линтерами (ruff)
- Запуска тестов
- Автоматического деплоя при пуше в main

Линтеры запускаются перед деплоем - при ошибках деплой не выполняется.

## Структура проекта

```
events-provider-api/
├── alembic/              # Миграции БД
│   └── versions/
├── app/
│   ├── api/              # API endpoints
│   ├── client/           # HTTP клиенты (Events Provider, Capashino)
│   ├── config/           # Конфигурация (логирование)
│   ├── repositories/     # Репозитории для работы с БД
│   ├── schemes/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   ├── workers/          # Фоновые воркеры (outbox)
│   ├── database.py       # Настройка БД
│   ├── exceptions.py     # Кастомные исключения
│   ├── main.py           # Точка входа FastAPI
│   ├── models.py         # SQLAlchemy модели
│   ├── settings.py       # Настройки приложения
│   └── types.py          # Типы и Enum'ы
├── logs/                 # Логи приложения
├── tests/                # Тесты
├── .env                  # Переменные окружения (не в git)
├── .gitignore
├── .pre-commit-config.yaml
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml        # Конфигурация проекта и ruff
├── pytest.ini
├── README.md
└── requirements.txt
```

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| `POSTGRES_DATABASE_NAME` | Имя БД | `events_db` |
| `POSTGRES_HOST` | Хост PostgreSQL | `localhost` |
| `POSTGRES_PORT` | Порт PostgreSQL | `5433` |
| `POSTGRES_USERNAME` | Пользователь БД | `postgres` |
| `POSTGRES_PASSWORD` | Пароль БД | `admin` |
| `EVENTS_PROVIDER_API_URL` | URL Events Provider API | - |
| `X_API_KEY` | API ключ для Events Provider | - |
| `CAPASHINO_BASE_URL` | URL Capashino API | `https://capashino.dev-2.python-labs.ru` |
| `CAPASHINO_API_KEY` | API ключ для Capashino | - |
| `OUTBOX_WORKER_INTERVAL` | Интервал опроса outbox (сек) | `10` |
| `OUTBOX_MAX_ATTEMPTS` | Макс. попыток отправки | `5` |
| `SENTRY_DSN` | DSN для GlitchTip | `None` |
| `SENTRY_ENVIRONMENT` | Окружение для Sentry | `production` |
| `SENTRY_TRACES_SAMPLE_RATE` | Частота трейсов | `1.0` |

## Лицензия

MIT