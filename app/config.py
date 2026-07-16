import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    APP_VERSION = os.environ.get("APP_VERSION", "1.0.0")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Low-entropy placeholder for local dev only; real values belong in .env
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-placeholder")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "testing"
    JWT_SECRET_KEY = "testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "")


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str):
    """Return the config class for the given environment name."""
    try:
        return _CONFIGS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown config name: {name!r}") from exc
