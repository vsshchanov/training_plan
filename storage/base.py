"""
Абстрактный базовый класс для всех хранилищ.
Определяет интерфейс, который должны реализовать все хранилища.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

class BaseStorage(ABC):

    @abstractmethod
    def get_all_workout_days(self) -> list[dict]:
        ...

    @abstractmethod
    def get_workout_day(self, day_id: str) -> Optional[dict]:
        ...

    @abstractmethod
    def create_workout_day(self, date: str, name: str) -> dict:
        ...

    @abstractmethod
    def update_workout_day(self, day_id: str, date: str, name: str) -> Optional[dict]:
        ...

    @abstractmethod
    def delete_workout_day(self, day_id: str) -> bool:
        ...

    @abstractmethod
    def add_exercise(self, day_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        """Добавляет упражнение с набором подходов. Каждый set: {reps, weight (optional), rest_time (optional)}"""
        ...

    @abstractmethod
    def update_exercise(self, day_id: str, exercise_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        """Обновляет название и полностью заменяет подходы упражнения."""
        ...

    @abstractmethod
    def delete_exercise(self, day_id: str, exercise_id: str) -> bool:
        ...

    @abstractmethod
    def copy_workout_day(self, day_id: str, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def get_templates(self, user_id: int) -> List[dict]:
        ...

    @abstractmethod
    def create_template(self, user_id: int, name: str, exercises: List[dict]) -> dict:
        ...

    @abstractmethod
    def delete_template(self, template_id: str, user_id: int) -> bool:
        ...

    @abstractmethod
    def create_workout_from_template(self, template_id: str, user_id: int, date: str) -> Optional[dict]:
        ...

    @abstractmethod
    def reorder_exercises(self, day_id: str, exercise_ids: List[str], user_id: int) -> bool:
        ...

    @abstractmethod
    def get_exercise_names(self, user_id: int) -> List[str]:
        ...

    @abstractmethod
    def get_exercise_progress(self, user_id: int, exercise_name: str) -> List[dict]:
        ...

    # ─── Питание ───
    @abstractmethod
    def get_nutrition_profile(self, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def upsert_nutrition_profile(self, user_id: int, data: dict) -> dict:
        ...

    @abstractmethod
    def get_nutrition_days(self, user_id: int) -> List[dict]:
        ...

    @abstractmethod
    def get_or_create_nutrition_day(self, user_id: int, date: str) -> dict:
        ...

    @abstractmethod
    def delete_nutrition_day(self, day_id: str, user_id: int) -> bool:
        ...

    @abstractmethod
    def create_meal(self, day_id: str, meal_type: str, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def delete_meal(self, day_id: str, meal_id: str, user_id: int) -> bool:
        ...

    @abstractmethod
    def add_food_item(self, meal_id: str, data: dict, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def update_food_item(self, meal_id: str, food_id: str, data: dict, user_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def delete_food_item(self, meal_id: str, food_id: str, user_id: int) -> bool:
        ...