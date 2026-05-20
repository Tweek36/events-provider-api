# Events Provider API

FastAPI приложение для работы с событиями.

## Требования

- Python 3.11+
- Docker и Docker Compose (для запуска в контейнере)
- [uv](https://docs.astral.sh/uv/) (для локальной разработки)

## Установка для локальной разработки

### 1. Установка uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Установка зависимостей

```bash
# Установка основных зависимостей
uv sync

# Установка с dev-зависимостями (включая pre-commit)
uv sync --all-extras
```

### 3. Настройка pre-commit

```bash
# Установка git hooks
uv run pre-commit install

# Запуск проверки на всех файлах (опционально)
uv run pre-commit run --all-files
```

## Запуск приложения

### Локально

```bash
# Активация виртуального окружения
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate  # Windows

# Запуск сервера
uvicorn app.main:app --reload
```

### С помощью Docker

```bash
# Сборка и запуск
docker-compose up --build

# Запуск в фоновом режиме
docker-compose up -d
```

## Разработка

### Pre-commit hooks

Проект использует pre-commit для автоматической проверки кода перед коммитом:

- **ruff** - линтинг и форматирование кода
- **trailing-whitespace** - удаление пробелов в конце строк
- **end-of-file-fixer** - проверка переноса строки в конце файлов
- **check-yaml** - валидация YAML файлов
- **check-toml** - валидация TOML файлов
- **check-json** - валидация JSON файлов
- **check-added-large-files** - предотвращение коммита больших файлов
- **check-merge-conflict** - проверка маркеров конфликтов слияния

### Запуск линтера вручную

```bash
# Проверка и автоисправление
uv run ruff check --fix .

# Форматирование кода
uv run ruff format .
```

### Запуск тестов

```bash
uv run pytest
```

## Структура проекта

```
.
├── app/                    # Основной код приложения
│   ├── api/               # API endpoints
│   ├── client/            # Клиенты для внешних сервисов
│   ├── config/            # Конфигурация
│   ├── models.py          # Модели базы данных
│   ├── repositories/      # Репозитории для работы с БД
│   ├── schemes/           # Pydantic схемы
│   └── services/          # Бизнес-логика
├── alembic/               # Миграции базы данных
├── tests/                 # Тесты
├── pyproject.toml         # Конфигурация проекта и зависимости
└── docker-compose.yml     # Docker конфигурация
```

## Миграции базы данных

```bash
# Создание новой миграции
uv run alembic revision --autogenerate -m "описание изменений"

# Применение миграций
uv run alembic upgrade head

# Откат последней миграции
uv run alembic downgrade -1
```

## Переменные окружения

Создайте файл `.env` на основе `.env.example` (если есть) и настройте необходимые переменные.

## Лицензия

[Укажите лицензию проекта]
