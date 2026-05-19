"""
Главный файл Flask-приложения.
Запуск: python app.py
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import STORAGE_TYPE, POSTGRES_CONFIG
from storage.postgres_storage import PostgresStorage, UserModel

app = Flask(__name__)
app.secret_key = "super-secret-key-change-in-production"  # замените на случайную строку

# Инициализация хранилища (только PostgreSQL для многопользовательского режима)
storage = PostgresStorage(**POSTGRES_CONFIG)
print("[INFO] Используется хранилище: PostgreSQL")

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = None  # будем обрабатывать на фронтенде

@login_manager.user_loader
def load_user(user_id):
    return storage.get_user_by_id(int(user_id))

# ─────────────────────────────────
#  Страницы
# ─────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ─────────────────────────────────
#  API: Аутентификация
# ─────────────────────────────────
@app.route("/api/register", methods=["POST"])
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

# ─────────────────────────────────
#  API: Тренировки (все требуют авторизации)
# ─────────────────────────────────
@app.route("/api/workouts", methods=["GET"])
@login_required
def get_workouts():
    days = storage.get_all_workout_days(current_user.id)
    return jsonify(days)

@app.route("/api/workouts", methods=["POST"])
@login_required
def create_workout():
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    new_day = storage.create_workout_day(data["date"], data["name"], current_user.id)
    return jsonify(new_day), 201

@app.route("/api/workouts/<day_id>", methods=["PUT"])
@login_required
def update_workout(day_id):
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    updated = storage.update_workout_day(day_id, data["date"], data["name"], current_user.id)
    if updated is None:
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>", methods=["DELETE"])
@login_required
def delete_workout(day_id):
    success = storage.delete_workout_day(day_id, current_user.id)
    if not success:
        return jsonify({"error": "День не найден или доступ запрещён"}), 404
    return jsonify({"message": "День удалён"})

@app.route("/api/workouts/<day_id>/exercises", methods=["POST"])
@login_required
def add_exercise(day_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    # ... (валидация как раньше)
    exercise = storage.add_exercise(day_id, data["name"], data["sets"], current_user.id)
    if exercise is None:
        return jsonify({"error": "Тренировочный день не найден или доступ запрещён"}), 404
    return jsonify(exercise), 201

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["PUT"])
@login_required
def update_exercise(day_id, exercise_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    updated = storage.update_exercise(day_id, exercise_id, data["name"], data["sets"], current_user.id)
    if updated is None:
        return jsonify({"error": "Упражнение не найдено или доступ запрещён"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["DELETE"])
@login_required
def delete_exercise(day_id, exercise_id):
    success = storage.delete_exercise(day_id, exercise_id, current_user.id)
    if not success:
        return jsonify({"error": "Упражнение не найдено или доступ запрещён"}), 404
    return jsonify({"message": "Упражнение удалено"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)