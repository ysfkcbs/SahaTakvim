import os
from datetime import timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_SQLITE_PATH = INSTANCE_DIR / "app.db"


def build_database_uri():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        # Render/Heroku compatibility
        if database_url.startswith("postgres://"):
            return database_url.replace("postgres://", "postgresql://", 1)

        # Normalize relative sqlite paths to absolute paths so SQLite can always open the file.
        if database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
            raw_path = database_url.replace("sqlite:///", "", 1)
            abs_path = (BASE_DIR / raw_path).resolve()
            abs_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{abs_path.as_posix()}"

        return database_url

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SQLALCHEMY_DATABASE_URI = build_database_uri()


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
