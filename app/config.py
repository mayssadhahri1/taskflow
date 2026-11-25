"""Configuration lue depuis les variables d'environnement (principe 12-factor)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./taskflow.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-a-remplacer-en-production-0123456789")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    app_version: str = os.getenv("APP_VERSION", "1.0.0")


settings = Settings()
