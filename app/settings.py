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

DATABASE_URL = settings.DATABASE_URL
REDIS_URL = settings.REDIS_URL
EVENTS_PROVIDER_API_URL = settings.EVENTS_PROVIDER_API_URL
X_API_KEY = settings.X_API_KEY
HOSTNAME = settings.HOSTNAME