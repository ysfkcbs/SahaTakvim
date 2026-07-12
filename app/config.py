import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SQLITE_PATH = INSTANCE_DIR / "app.db"

load_dotenv(BASE_DIR / ".env")


def build_database_uri():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        # Some providers expose PostgreSQL URLs with the legacy postgres:// scheme.
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)

        # Normalize relative sqlite paths to absolute paths so SQLite can always open the file.
        if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
            raw_path = database_url.replace("sqlite:///", "", 1)
            abs_path = (BASE_DIR / raw_path).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{abs_path.as_posix()}"

        return database_url

    if os.getenv("FLASK_ENV", "development") == "production":
        raise RuntimeError("DATABASE_URL must be set in production. Refusing to use ephemeral SQLite storage.")

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SESSION_COOKIE_NAME = "saha_takvim_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    _COOKIE_SECURE_DEFAULT = os.getenv("FLASK_ENV", "development") == "production"
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", _COOKIE_SECURE_DEFAULT)
    REMEMBER_COOKIE_SECURE = env_bool("REMEMBER_COOKIE_SECURE", _COOKIE_SECURE_DEFAULT)


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
