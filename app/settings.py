from pydantic_settings import BaseSettings
from pydantic import ConfigDict, HttpUrl

class Settings(BaseSettings):
    POSTGRES_DATABASE_NAME: str = "events_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USERNAME: str = "postgres"
    POSTGRES_PASSWORD: str = "admin"
    REDIS_URL: str = "redis://localhost:6379/0"
    EVENTS_PROVIDER_API_URL: HttpUrl = HttpUrl("https://api.events-provider.com")
    X_API_KEY: str = "your-api-key"
    HOSTNAME: str = "localhost"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
