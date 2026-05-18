"""
Главный файл Flask-приложения.
Запуск: python app.py
"""

from flask import Flask, render_template, request, jsonify
from config import STORAGE_TYPE, JSON_FILE_PATH, POSTGRES_CONFIG
from storage.json_storage import JsonStorage
from storage.postgres_storage import PostgresStorage

app = Flask(__name__)

if STORAGE_TYPE == "postgresql":
    storage = PostgresStorage(**POSTGRES_CONFIG)
    print("[INFO] Используется хранилище: PostgreSQL")
else:
    storage = JsonStorage(JSON_FILE_PATH)
    print("[INFO] Используется хранилище: JSON-файл")

@app.route("/")
def index():
    return render_template("index.html", storage_type=STORAGE_TYPE)

@app.route("/api/workouts", methods=["GET"])
def get_workouts():
    return jsonify(storage.get_all_workout_days())

@app.route("/api/workouts", methods=["POST"])
def create_workout():
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    new_day = storage.create_workout_day(data["date"], data["name"])
    return jsonify(new_day), 201

@app.route("/api/workouts/<day_id>", methods=["PUT"])
def update_workout(day_id):
    data = request.get_json()
    if not data or "date" not in data or "name" not in data:
        return jsonify({"error": "Поля 'date' и 'name' обязательны"}), 400
    updated = storage.update_workout_day(day_id, data["date"], data["name"])
    if updated is None:
        return jsonify({"error": "День не найден"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>", methods=["DELETE"])
def delete_workout(day_id):
    success = storage.delete_workout_day(day_id)
    if not success:
        return jsonify({"error": "День не найден"}), 404
    return jsonify({"message": "День удалён"}), 200

# ── Упражнения (с подходами) ──
@app.route("/api/workouts/<day_id>/exercises", methods=["POST"])
def add_exercise(day_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    sets = data["sets"]
    if not isinstance(sets, list) or len(sets) == 0:
        return jsonify({"error": "Поле 'sets' должно быть непустым массивом подходов"}), 400
    for s in sets:
        if "reps" not in s:
            return jsonify({"error": "Каждый подход должен содержать 'reps'"}), 400
        try:
            int(s["reps"])
        except (ValueError, TypeError):
            return jsonify({"error": "Поле 'reps' должно быть целым числом"}), 400
        if "weight" in s and s["weight"] is not None:
            try:
                float(s["weight"])
            except (ValueError, TypeError):
                return jsonify({"error": "Поле 'weight' должно быть числом"}), 400
        if "rest_time" in s and s["rest_time"] is not None:
            try:
                int(s["rest_time"])
            except (ValueError, TypeError):
                return jsonify({"error": "Поле 'rest_time' должно быть целым числом (секунды)"}), 400
    exercise = storage.add_exercise(day_id, data["name"], sets)
    if exercise is None:
        return jsonify({"error": "Тренировочный день не найден"}), 404
    return jsonify(exercise), 201

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["PUT"])
def update_exercise(day_id, exercise_id):
    data = request.get_json()
    if not data or "name" not in data or "sets" not in data:
        return jsonify({"error": "Поля 'name' и 'sets' обязательны"}), 400
    sets = data["sets"]
    if not isinstance(sets, list) or len(sets) == 0:
        return jsonify({"error": "Поле 'sets' должно быть непустым массивом подходов"}), 400
    # Валидация аналогичная
    for s in sets:
        if "reps" not in s:
            return jsonify({"error": "Каждый подход должен содержать 'reps'"}), 400
        try:
            int(s["reps"])
        except (ValueError, TypeError):
            return jsonify({"error": "Поле 'reps' должно быть целым числом"}), 400
        if "weight" in s and s["weight"] is not None:
            try:
                float(s["weight"])
            except (ValueError, TypeError):
                return jsonify({"error": "Поле 'weight' должно быть числом"}), 400
        if "rest_time" in s and s["rest_time"] is not None:
            try:
                int(s["rest_time"])
            except (ValueError, TypeError):
                return jsonify({"error": "Поле 'rest_time' должно быть целым числом (секунды)"}), 400
    updated = storage.update_exercise(day_id, exercise_id, data["name"], sets)
    if updated is None:
        return jsonify({"error": "Упражнение или день не найдены"}), 404
    return jsonify(updated)

@app.route("/api/workouts/<day_id>/exercises/<exercise_id>", methods=["DELETE"])
def delete_exercise(day_id, exercise_id):
    success = storage.delete_exercise(day_id, exercise_id)
    if not success:
        return jsonify({"error": "Упражнение или день не найдены"}), 404
    return jsonify({"message": "Упражнение удалено"}), 200

@app.route("/api/storage-info", methods=["GET"])
def storage_info():
    return jsonify({"storage_type": STORAGE_TYPE})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)