from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Custom Auth Access Control API"
    app_env: str = "local"
    database_url: str = "sqlite:///./local.db"
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    admin_email: str = "admin@example.com"
    admin_password: str = "Admin123!"
    manager_email: str = "manager@example.com"
    manager_password: str = "Manager123!"
    user_email: str = "user@example.com"
    user_password: str = "User123!"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
