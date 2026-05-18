"""
Хранилище данных в JSON-файле.
"""

import json
import os
import uuid
import threading
from typing import Optional, List
from storage.base import BaseStorage

class JsonStorage(BaseStorage):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lock = threading.Lock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            self._write_data({"workout_days": []})

    def _read_data(self) -> dict:
        with self.lock:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def _write_data(self, data: dict) -> None:
        with self.lock:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def get_all_workout_days(self) -> list[dict]:
        data = self._read_data()
        days = data.get("workout_days", [])
        days.sort(key=lambda d: d["date"], reverse=True)
        return days

    def get_workout_day(self, day_id: str) -> Optional[dict]:
        data = self._read_data()
        for day in data.get("workout_days", []):
            if day["id"] == day_id:
                return day
        return None

    def create_workout_day(self, date: str, name: str) -> dict:
        data = self._read_data()
        new_day = {
            "id": str(uuid.uuid4()),
            "date": date,
            "name": name,
            "exercises": [],
        }
        data["workout_days"].append(new_day)
        self._write_data(data)
        return new_day

    def update_workout_day(self, day_id: str, date: str, name: str) -> Optional[dict]:
        data = self._read_data()
        for day in data.get("workout_days", []):
            if day["id"] == day_id:
                day["date"] = date
                day["name"] = name
                self._write_data(data)
                return day
        return None

    def delete_workout_day(self, day_id: str) -> bool:
        data = self._read_data()
        initial_len = len(data["workout_days"])
        data["workout_days"] = [d for d in data["workout_days"] if d["id"] != day_id]
        if len(data["workout_days"]) < initial_len:
            self._write_data(data)
            return True
        return False

    def add_exercise(self, day_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        data = self._read_data()
        for day in data.get("workout_days", []):
            if day["id"] == day_id:
                exercise = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "sets": []
                }
                for s in sets:
                    exercise["sets"].append({
                        "id": str(uuid.uuid4()),
                        "reps": int(s["reps"]),
                        "weight": float(s["weight"]) if s.get("weight") is not None else None,
                        "rest_time": int(s["rest_time"]) if s.get("rest_time") is not None else None,
                    })
                day["exercises"].append(exercise)
                self._write_data(data)
                return exercise
        return None

    def update_exercise(self, day_id: str, exercise_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        data = self._read_data()
        for day in data.get("workout_days", []):
            if day["id"] == day_id:
                for ex in day["exercises"]:
                    if ex["id"] == exercise_id:
                        ex["name"] = name
                        ex["sets"] = []
                        for s in sets:
                            ex["sets"].append({
                                "id": str(uuid.uuid4()),  # новые id для сетов при полной замене
                                "reps": int(s["reps"]),
                                "weight": float(s["weight"]) if s.get("weight") is not None else None,
                                "rest_time": int(s["rest_time"]) if s.get("rest_time") is not None else None,
                            })
                        self._write_data(data)
                        return ex
        return None

    def delete_exercise(self, day_id: str, exercise_id: str) -> bool:
        data = self._read_data()
        for day in data.get("workout_days", []):
            if day["id"] == day_id:
                initial_len = len(day["exercises"])
                day["exercises"] = [e for e in day["exercises"] if e["id"] != exercise_id]
                if len(day["exercises"]) < initial_len:
                    self._write_data(data)
                    return True
        return False