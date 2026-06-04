FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Генерируем иконки PWA, запускаем миграции, затем приложение через gunicorn
CMD python generate_icons.py && alembic upgrade head && gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 60 app:app
