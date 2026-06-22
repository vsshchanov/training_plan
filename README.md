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
git clone https://github.com/your-repo/training_plan.git
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
