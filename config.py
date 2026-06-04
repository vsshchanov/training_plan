"""
Конфигурация приложения.
Для Docker: все параметры берутся из переменных окружения.
По умолчанию используется PostgreSQL.
"""

import os
import urllib.parse

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "postgresql")

_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    _parsed = urllib.parse.urlparse(_db_url)
    POSTGRES_CONFIG = {
        "host": _parsed.hostname,
        "port": _parsed.port or 5432,
        "database": _parsed.path.lstrip("/"),
        "user": _parsed.username,
        "password": _parsed.password,
    }
else:
    POSTGRES_CONFIG = {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", 5432)),
        "database": os.environ.get("POSTGRES_DB", "workout_tracker"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
    }

JSON_FILE_PATH = os.environ.get("JSON_FILE_PATH", "data/workouts.json")