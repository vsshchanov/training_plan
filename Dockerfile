FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Flask слушает на 5000

EXPOSE 5000

# Запуск приложения
CMD [ "python", "app.py" ]
