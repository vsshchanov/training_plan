"""
Конфигурация приложения.
Для Docker: все параметры берутся из переменных окружения.
По умолчанию используется PostgreSQL.
"""

import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

STORAGE_TYPE = os.environ.get("STORAGE_TYPE", "postgresql")

POSTGRES_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    "database": os.environ.get("POSTGRES_DB", "workout_tracker"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
}

JSON_FILE_PATH = os.environ.get("JSON_FILE_PATH", "data/workouts.json")