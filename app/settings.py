from pydantic import ConfigDict, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DATABASE_NAME: str = "events_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USERNAME: str = "postgres"
    POSTGRES_PASSWORD: str = "admin"
    EVENTS_PROVIDER_API_URL: HttpUrl = HttpUrl("https://api.events-provider.com")
    X_API_KEY: str = "your-api-key"
    HOSTNAME: str = "localhost"

    # Outbox worker settings
    OUTBOX_WORKER_INTERVAL: int = 10
    OUTBOX_MAX_ATTEMPTS: int = 5

    # Capashino settings
    CAPASHINO_BASE_URL: HttpUrl = HttpUrl("https://capashino.dev-2.python-labs.ru")
    CAPASHINO_API_KEY: str = "your-capashino-api-key"

    # GlitchTip/Sentry settings
    SENTRY_DSN: str | None = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
