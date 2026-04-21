"""
Application configuration module.
Extended with JWT, AI (Gemini), and multi-channel notification settings.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings:
    """Centralized application settings loaded from environment variables."""

    # ── Database ──────────────────────────────────────────────
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "rubiscape_alerts")
    DB_TYPE: str = os.getenv("DB_TYPE", "mysql")

    @property
    def DATABASE_URL(self) -> str:
        if self.DB_TYPE.lower() == "sqlite":
            db_path = BASE_DIR / f"{self.DB_NAME}.db"
            return f"sqlite:///{db_path}"
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"mysql+pymysql://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── Application ───────────────────────────────────────────
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    APP_DEBUG: bool = os.getenv("APP_DEBUG", "False").lower() in ("true", "1", "yes")

    # ── Notification ──────────────────────────────────────────
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.example.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "alerts@example.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "changeme")
    NOTIFICATION_EMAIL: str = os.getenv("NOTIFICATION_EMAIL", "admin@example.com")

    # ── Slack & Webhook ───────────────────────────────────────
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    GENERIC_WEBHOOK_URL: str = os.getenv("GENERIC_WEBHOOK_URL", "")

    # ── JWT Authentication ────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "rubiscape-super-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # ── AI Features ───────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")



settings = Settings()
