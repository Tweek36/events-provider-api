from pydantic_settings import BaseSettings
from pydantic import ConfigDict, HttpUrl

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    EVENTS_PROVIDER_API_URL: HttpUrl
    X_API_KEY: str
    HOSTNAME: str

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
