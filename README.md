# Workout & Nutrition Tracker

Веб-приложение для отслеживания тренировок и питания. Записывайте тренировки, считайте калории, следите за балансом КБЖУ.

## Возможности

### Тренировки
- Создание тренировочных дней с датой, названием и заметками
- Упражнения с подходами (повторы, вес, время отдыха)
- Шаблоны тренировок — сохраните и используйте повторно
- Копирование тренировки на сегодня одним кликом
- Изменение порядка упражнений (стрелки вверх/вниз)
- Статистика прогресса по упражнениям (графики Chart.js)
- Личные рекорды по весу
- Группировка тренировок по месяцам
- Поиск и фильтрация по названию и датам
- Экспорт всех данных в CSV

### Питание (Нутрициолог)
- Калькулятор дневной нормы калорий по формуле Миффлина-Сан Жеора
- Параметры: пол, вес, рост, возраст, уровень активности, цель (похудение/поддержание/набор)
- Дневник приёмов пищи (завтрак, обед, ужин, перекус)
- Учёт КБЖУ каждого продукта (ввод на 100г + вес порции)
- Прогресс-бары калорий и макронутриентов (Б/Ж/У)
- Предупреждения при превышении дневной нормы
- Навигация по дням для просмотра истории питания

### ИМТ
- Калькулятор индекса массы тела
- Цветная шкала с категориями (дефицит / норма / избыток / ожирение)

### Общее
- Многопользовательская авторизация (логин/пароль)
- Toast-уведомления вместо браузерных alert
- Модалки подтверждения вместо confirm
- PWA — можно установить как приложение на телефон
- Мобильная адаптация
- Rate limiting на авторизацию (защита от перебора)

## Технологии

- **Backend:** Python, Flask, SQLAlchemy, PostgreSQL, Alembic
- **Frontend:** Vanilla JS, CSS, Chart.js
- **Инфраструктура:** Docker, Docker Compose, gunicorn, nginx (production)

## Быстрый старт (Docker)

```bash
git clone https://github.com/vsshchanov/training_plan.git
cd training_plan
```

Создайте файл `.env`:
```
SECRET_KEY=your-secret-key
POSTGRES_USER=workout_user
POSTGRES_PASSWORD=your-password
POSTGRES_DB=workout_tracker
NGROK_AUTHTOKEN=your-ngrok-token
```

Запуск (локальная разработка с ngrok):
```bash
docker compose up --build
```

| Сервис | Адрес |
|---|---|
| Приложение | http://localhost:5000 |
| ngrok (публичный URL) | http://localhost:4040 |
| PgAdmin | http://localhost:5050 |

## Деплой на VPS (production)

**1. Подключитесь к серверу:**
```bash
ssh root@ВАШ_IP
```

**2. Установите зависимости:**
```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose nginx git
```

**3. Склонируйте репозиторий:**
```bash
git clone -b nutritionist https://github.com/vsshchanov/training_plan.git /opt/workout-app
cd /opt/workout-app
```

**4. Создайте файл с секретами:**
```bash
nano /opt/workout-app/.env.prod
```
```
SECRET_KEY=ваша-длинная-случайная-строка
POSTGRES_USER=workout_user
POSTGRES_PASSWORD=ваш-надёжный-пароль
POSTGRES_DB=workout_tracker
```

**5. Запустите приложение:**
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

**6. Настройте Nginx:**
```bash
nano /etc/nginx/sites-available/workout
```
```nginx
server {
    listen 80;
    server_name ВАШ_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
```bash
ln -s /etc/nginx/sites-available/workout /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

**7. Готово:** откройте `http://ВАШ_IP` в браузере.

## Управление сервером

```bash
ssh root@ВАШ_IP
cd /opt/workout-app
```

| Действие | Команда |
|---|---|
| Логи приложения | `docker-compose -f docker-compose.prod.yml logs --tail 20 web` |
| Остановить | `docker-compose -f docker-compose.prod.yml down` |
| Запустить | `docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d` |
| Обновить до новой версии | `git pull && docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| Удалить всё (включая БД) | `docker-compose -f docker-compose.prod.yml down -v` |

## Перенос локальной БД на сервер

На вашем ПК:
```bash
docker exec workout_db pg_dump -U workout_user --encoding=UTF8 workout_tracker > backup.sql
scp backup.sql root@ВАШ_IP:/opt/workout-app/
```

На сервере:
```bash
docker exec -i workout-app_db_1 psql -U workout_user workout_tracker < /opt/workout-app/backup.sql
```

## Просмотр базы данных

Через терминал на сервере:
```bash
docker exec -it workout-app_db_1 psql -U workout_user workout_tracker
```

Полезные команды psql:
```sql
\dt                           -- список таблиц
SELECT * FROM users;          -- пользователи
SELECT * FROM workout_days;   -- тренировки
SELECT * FROM nutrition_days; -- дни питания
\q                            -- выйти
```

Через SSH-туннель (для подключения DBeaver/pgAdmin с ПК):
```bash
ssh -L 5433:127.0.0.1:5432 root@ВАШ_IP
```
Затем подключитесь к `localhost:5433` в любом клиенте БД.

## Структура проекта

```
app.py                  — Flask-сервер, API-эндпоинты
config.py               — конфигурация из переменных окружения
storage/
  base.py               — абстрактный интерфейс хранилища
  postgres_storage.py    — SQLAlchemy модели и CRUD-методы
templates/
  index.html            — единственная HTML-страница (SPA)
static/
  js/app.js             — вся клиентская логика
  css/style.css         — стили
  sw.js                 — Service Worker (PWA)
  manifest.json         — PWA-манифест
migrations/
  versions/             — Alembic-миграции
docker-compose.yml      — локальная разработка (web + db + ngrok + pgadmin)
docker-compose.prod.yml — production (web + db, порт только на localhost)
Dockerfile              — сборка образа
```

## API-эндпоинты

### Аутентификация
- `POST /api/register` — регистрация
- `POST /api/login` — вход
- `POST /api/logout` — выход
- `GET /api/check-auth` — проверка сессии

### Тренировки
- `GET /api/workouts` — все тренировки
- `POST /api/workouts` — создать день
- `PUT /api/workouts/<id>` — обновить день
- `DELETE /api/workouts/<id>` — удалить день
- `POST /api/workouts/<id>/copy` — копировать на сегодня
- `POST /api/workouts/<id>/exercises` — добавить упражнение
- `PUT /api/workouts/<id>/exercises/<eid>` — обновить упражнение
- `DELETE /api/workouts/<id>/exercises/<eid>` — удалить упражнение
- `PUT /api/workouts/<id>/exercises/reorder` — изменить порядок

### Шаблоны
- `GET /api/templates` — список шаблонов
- `POST /api/templates` — создать шаблон
- `DELETE /api/templates/<id>` — удалить шаблон
- `POST /api/templates/<id>/use` — создать тренировку из шаблона

### Статистика и экспорт
- `GET /api/stats/exercises` — список упражнений
- `GET /api/stats/progress?exercise=<name>` — прогресс по упражнению
- `GET /api/export` — скачать CSV

### Питание
- `GET /api/nutrition/profile` — профиль (нормы КБЖУ)
- `POST /api/nutrition/profile` — создать/обновить профиль
- `GET /api/nutrition/today?date=YYYY-MM-DD` — день питания
- `GET /api/nutrition/days` — все дни
- `DELETE /api/nutrition/days/<id>` — удалить день
- `POST /api/nutrition/days/<id>/meals` — добавить приём пищи
- `DELETE /api/nutrition/days/<id>/meals/<mid>` — удалить приём пищи
- `POST /api/nutrition/meals/<mid>/foods` — добавить продукт
- `PUT /api/nutrition/meals/<mid>/foods/<fid>` — обновить продукт
- `DELETE /api/nutrition/meals/<mid>/foods/<fid>` — удалить продукт

## Ветки

| Ветка | Описание |
|---|---|
| `main` | Стабильная версия с тренировками |
| `app_on_server` | main + подготовка к деплою на VPS (gunicorn, docker-compose.prod.yml) |
| `nutritionist` | app_on_server + модуль питания и ИМТ |
| `develop` | Ветка разработки |
