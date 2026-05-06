from pydantic_settings import BaseSettings
from pydantic import ConfigDict, HttpUrl

class Settings(BaseSettings):
    POSTGRES_CONNECTION_STRING: str = "postgresql+asyncpg://postgres:admin@localhost:5433/events_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    EVENTS_PROVIDER_API_URL: HttpUrl = HttpUrl("https://api.events-provider.com")
    X_API_KEY: str = "your-api-key"
    HOSTNAME: str = "localhost"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
