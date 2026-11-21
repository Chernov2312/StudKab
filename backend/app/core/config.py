from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://puls@localhost/puls"
    celery_broker_url: str = "redis://localhost:6379/0"
    app_origin: str = "http://localhost:8080"
    app_env: Literal["development", "production"] = "development"
    session_ttl_seconds: int = Field(default=7 * 24 * 3600, ge=60)
    login_window_seconds: int = Field(default=900, ge=60, le=86_400)
    login_username_limit: int = Field(default=8, ge=1)
    login_address_limit: int = Field(default=40, ge=1)

    @property
    def secure_cookie(self) -> bool:
        return self.app_env == "production" or self.app_origin.startswith("https://")

    @property
    def cookie_name(self) -> str:
        return "__Host-session" if self.secure_cookie else "puls-session"

    @model_validator(mode="after")
    def validate_origin(self) -> "Settings":
        from urllib.parse import urlsplit

        origin = urlsplit(self.app_origin)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.hostname
            or origin.username is not None
            or origin.path
            or origin.query
            or origin.fragment
            or (self.app_env == "production" and origin.scheme != "https")
        ):
            raise ValueError(
                "APP_ORIGIN must be a single HTTP(S) origin; production requires HTTPS"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
