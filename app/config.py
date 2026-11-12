"""SubSentry Enterprise settings — plain Python, no pydantic-settings.

Reads configuration from the environment (`.env` is loaded by
``app/__init__.py`` before anything reads credentials). Defaults are safe
for local development; SECRET_KEY must be overridden in production.
"""
import logging
import os

logger = logging.getLogger(__name__)


def _env(name, default=None):
    value = os.environ.get(name)
    return default if value is None or value == "" else value


class Settings:
    DATABASE_URL: str = _env("DATABASE_URL", "sqlite:///./subsentry.db")
    SECRET_KEY: str = _env("SECRET_KEY", "dev-secret-change-me")
    JWT_ALGORITHM: str = _env("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(_env("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    PAYPAL_MODE: str = _env("PAYPAL_MODE", "")
    PAYPAL_CLIENT_ID: str | None = _env("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET: str | None = _env("PAYPAL_CLIENT_SECRET")
    SMTP_HOST: str | None = _env("SMTP_HOST")
    SMTP_PORT: int = int(_env("SMTP_PORT", "587"))
    SMTP_USER: str | None = _env("SMTP_USER")
    SMTP_PASSWORD: str | None = _env("SMTP_PASSWORD")
    SMTP_FROM: str | None = _env("SMTP_FROM")
    LLM_PROVIDER: str = _env("LLM_PROVIDER", "template")
    LLM_API_KEY: str | None = _env("LLM_API_KEY")
    LLM_BASE_URL: str = _env("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions")
    LLM_MODEL: str = _env("LLM_MODEL", "gpt-4o-mini")

    def __init__(self):
        if self.SECRET_KEY == "dev-secret-change-me":
            logger.warning(
                "SECRET_KEY is the insecure default 'dev-secret-change-me' — "
                "set a real SECRET_KEY in the environment before deploying."
            )


settings = Settings()
