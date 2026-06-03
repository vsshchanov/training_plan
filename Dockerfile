FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# Генерируем иконки PWA, запускаем миграции, затем приложение
CMD python generate_icons.py && alembic upgrade head && python app.py
