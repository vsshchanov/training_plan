"""
Главный файл Flask-приложения.
"""

import csv
import io
from datetime import date
from flask import Flask, render_template, request, jsonify, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import STORAGE_TYPE, POSTGRES_CONFIG, SECRET_KEY
from storage.postgres_storage import PostgresStorage, UserModel

app = Flask(__name__)
app.secret_key = SECRET_KEY

storage = PostgresStorage(**POSTGRES_CONFIG)
print("[INFO] Используется хранилище: PostgreSQL")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

@login_manager.user_loader
def load_user(user_id):
    return storage.get_user_by_id(int(user_id))

# ── Страницы ──
@app.route("/")
def index():
    return render_template("index.html")

# ── Аутентификация ──
@app.route("/api/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Поля username и password обязательны"}), 400
    username = data["username"].strip()
    password = data["password"].strip()
    if len(username) < 3 or len(password) < 4:
        return jsonify({"error": "Логин минимум 3 символа, пароль минимум 4"}), 400
    user = storage.create_user(username, password)
    if user is None:
        return jsonify({"error": "Пользователь с таким именем уже существует"}), 409
    login_user(user)
    return jsonify({"message": "Регистрация успешна", "user": {"id": user.id, "username": user.username}}), 201

@app.route("/api/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({"error": "Поля username и password обязательны"}), 400
    user = storage.get_user_by_username(data["username"])
    if user and user.check_password(data["password"]):
        login_user(user)
        return jsonify({"message": "Вход выполнен", "user": {"id": user.id, "username": user.username}})
    return jsonify({"error": "Неверный логин или пароль"}), 401

@app.route("/api/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Вы вышли"})

@app.route("/api/check-auth", methods=["GET"])
def check_auth():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "user": {"id": current_user.id, "username": current_user.username}})
    return jsonify({"authenticated": False})

# ── Тренировки ──
@app.route("/api/workouts", methods=["GET"])
@login_required
def get_workouts():
    return jsonify(storage.get_all_workout_days(current_user.id))

@app.route("/api/workouts", methods=["POST"])
@login_required
def create_workout():
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    notes = data.get("notes") or None
    new_day = storage.create_workout_day(data["date"], data["name"], current_user.id, notes=notes)
    return jsonify(new_day), 201

@app.route("/api/workouts/<day_id>", methods=["PUT"])
@login_required
def update_workout(day_id):
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    notes = data.get("notes") or None
    updated = storage.update_workout_day(day_id, data["date"], data["name"], current_user.id, notes=notes)
    if updated is None:
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>", methods=["DELETE"])
@login_required
def delete_workout(day_id):
    if not storage.delete_workout_day(day_id, current_user.id):
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify({"message": "День удалён"})

@app.route("/api/workouts/<day_id>/copy", methods=["POST"])
@login_required
def copy_workout(day_id):
    new_day = storage.copy_workout_day(day_id, current_user.id)
    if new_day is None:
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify(new_day), 201

# ── Упражнения ──
@app.route("/api/workouts/<day_id>/exercises/reorder", methods=["PUT"])
@login_required
def reorder_exercises(day_id):
    data = request.get_json()
    if not data or "exercise_ids" not in data:
        return jsonify({"error": "Поле 'exercise_ids' обязательно"}), 400
    if not storage.reorder_exercises(day_id, data["exercise_ids"], current_user.id):
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify({"message": "Порядок обновлён"})

@app.route("/api/workouts/<day_id>/exercises", methods=["POST"])
@login_required
def add_exercise(day_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    exercise = storage.add_exercise(day_id, data["name"], data["sets"], current_user.id,
                                    description=data.get("description"))
    if exercise is None:
        return jsonify({"error": "Тренировочный день не найден или доступ запрещён"}), 404
    return jsonify(exercise), 201

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["PUT"])
@login_required
def update_exercise(day_id, exercise_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    updated = storage.update_exercise(day_id, exercise_id, data["name"], data["sets"], current_user.id,
                                      description=data.get("description"))
    if updated is None:
        return jsonify({"error": "Упражнение не найдено или доступ запрещён"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["DELETE"])
@login_required
def delete_exercise(day_id, exercise_id):
    if not storage.delete_exercise(day_id, exercise_id, current_user.id):
        return jsonify({"error": "Упражнение не найдено или доступ запрещён"}), 404
    return jsonify({"message": "Упражнение удалено"})

# ── Шаблоны ──
@app.route("/api/templates", methods=["GET"])
@login_required
def get_templates():
    return jsonify(storage.get_templates(current_user.id))

@app.route("/api/templates", methods=["POST"])
@login_required
def create_template():
    data = request.get_json()
    if not data or "name" not in data or "exercises" not in data:
        return jsonify({"error": "Поля 'name' и 'exercises' обязательны"}), 400
    tmpl = storage.create_template(current_user.id, data["name"].strip(), data["exercises"])
    return jsonify(tmpl), 201

@app.route("/api/templates/<template_id>", methods=["DELETE"])
@login_required
def delete_template(template_id):
    if not storage.delete_template(template_id, current_user.id):
        return jsonify({"error": "Шаблон не найден"}), 404
    return jsonify({"message": "Шаблон удалён"})

@app.route("/api/templates/<template_id>/use", methods=["POST"])
@login_required
def use_template(template_id):
    data = request.get_json() or {}
    target_date = data.get("date", date.today().isoformat())
    new_day = storage.create_workout_from_template(template_id, current_user.id, target_date)
    if new_day is None:
        return jsonify({"error": "Шаблон не найден"}), 404
    return jsonify(new_day), 201

# ── Статистика ──
@app.route("/api/stats/exercises", methods=["GET"])
@login_required
def get_exercise_names():
    return jsonify(storage.get_exercise_names(current_user.id))

@app.route("/api/stats/progress", methods=["GET"])
@login_required
def get_exercise_progress():
    name = request.args.get("exercise", "").strip()
    if not name:
        return jsonify({"error": "Параметр 'exercise' обязателен"}), 400
    return jsonify(storage.get_exercise_progress(current_user.id, name))

# ── Экспорт CSV ──
@app.route("/api/export", methods=["GET"])
@login_required
def export_csv():
    days = storage.get_all_workout_days(current_user.id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Дата", "Тренировка", "Заметки", "Упражнение", "Описание упражнения",
                     "Подход", "Повторы", "Вес (кг)", "Отдых (сек)"])
    for day in days:
        for ex in day.get("exercises", []):
            for i, s in enumerate(ex.get("sets", []), 1):
                writer.writerow([
                    day["date"], day["name"], day.get("notes") or "",
                    ex["name"], ex.get("description") or "",
                    i, s["reps"],
                    s["weight"] if s["weight"] is not None else "",
                    s["rest_time"] if s["rest_time"] is not None else "",
                ])
    output.seek(0)
    filename = f"workouts_{current_user.username}.csv"
    return Response(
        "﻿" + output.getvalue(),  # BOM для корректного открытия в Excel
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
