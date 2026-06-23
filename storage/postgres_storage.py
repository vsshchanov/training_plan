"""
Хранилище данных в PostgreSQL с использованием SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Date, Text, UniqueConstraint
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import uuid
from datetime import date as date_type

from storage.base import BaseStorage

Base = declarative_base()

# ---------- Модели таблиц ----------
class UserModel(Base, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    workout_days = relationship("WorkoutDayModel", back_populates="user", cascade="all, delete-orphan")
    nutrition_profile = relationship("NutritionProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    nutrition_days = relationship("NutritionDayModel", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
        }


class WorkoutDayModel(Base):
    __tablename__ = "workout_days"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    user = relationship("UserModel", back_populates="workout_days")
    exercises = relationship("ExerciseModel", back_populates="workout_day", cascade="all, delete-orphan",
                            order_by="ExerciseModel.order")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else "",
            "name": self.name,
            "notes": self.notes,
            "exercises": [ex.to_dict() for ex in self.exercises],
        }


class ExerciseModel(Base):
    __tablename__ = "exercises"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workout_day_id = Column(String(36), ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)

    workout_day = relationship("WorkoutDayModel", back_populates="exercises")
    sets = relationship("ExerciseSetModel", back_populates="exercise", cascade="all, delete-orphan",
                        order_by="ExerciseSetModel.order")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sets": [s.to_dict() for s in self.sets],
        }


class ExerciseSetModel(Base):
    __tablename__ = "exercise_sets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=True)
    rest_time = Column(Integer, nullable=True)  # секунды
    order = Column(Integer, nullable=False, default=0)

    exercise = relationship("ExerciseModel", back_populates="sets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reps": self.reps,
            "weight": self.weight,
            "rest_time": self.rest_time,
        }


class WorkoutTemplateModel(Base):
    __tablename__ = "workout_templates"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)

    exercises = relationship("TemplateExerciseModel", back_populates="template", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises],
        }


class TemplateExerciseModel(Base):
    __tablename__ = "template_exercises"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("workout_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, nullable=False, default=0)

    template = relationship("WorkoutTemplateModel", back_populates="exercises")
    sets = relationship("TemplateSetModel", back_populates="exercise", cascade="all, delete-orphan",
                        order_by="TemplateSetModel.order")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sets": [s.to_dict() for s in self.sets],
        }


class TemplateSetModel(Base):
    __tablename__ = "template_sets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey("template_exercises.id", ondelete="CASCADE"), nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=True)
    rest_time = Column(Integer, nullable=True)
    order = Column(Integer, nullable=False, default=0)

    exercise = relationship("TemplateExerciseModel", back_populates="sets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reps": self.reps,
            "weight": self.weight,
            "rest_time": self.rest_time,
        }


# ---------- Модели питания ----------
class NutritionProfileModel(Base):
    __tablename__ = "user_nutrition_profiles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    sex = Column(String(10), nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    age = Column(Integer, nullable=False)
    activity_level = Column(Float, nullable=False)
    goal = Column(String(20), nullable=False)

    user = relationship("UserModel", back_populates="nutrition_profile")

    def to_dict(self) -> dict:
        if self.sex == "male":
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age + 5
        else:
            bmr = 10 * self.weight + 6.25 * self.height - 5 * self.age - 161
        tdee = bmr * self.activity_level
        goal_mult = {"loss": 0.825, "maintenance": 1.0, "gain": 1.125}
        goal_cal = round(tdee * goal_mult.get(self.goal, 1.0))
        return {
            "id": self.id,
            "sex": self.sex,
            "weight": self.weight,
            "height": self.height,
            "age": self.age,
            "activity_level": self.activity_level,
            "goal": self.goal,
            "bmr": round(bmr),
            "tdee": round(tdee),
            "goal_calories": goal_cal,
            "protein_grams": round(goal_cal * 0.30 / 4),
            "fat_grams": round(goal_cal * 0.25 / 9),
            "carb_grams": round(goal_cal * 0.45 / 4),
        }


class NutritionDayModel(Base):
    __tablename__ = "nutrition_days"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_user_date"),)

    user = relationship("UserModel", back_populates="nutrition_days")
    meals = relationship("MealModel", back_populates="nutrition_day", cascade="all, delete-orphan",
                         order_by="MealModel.order")

    def to_dict(self) -> dict:
        meals_list = [m.to_dict() for m in self.meals]
        total_cal = sum(m["total_calories"] for m in meals_list)
        total_pro = sum(m["total_protein"] for m in meals_list)
        total_fat = sum(m["total_fat"] for m in meals_list)
        total_carb = sum(m["total_carbs"] for m in meals_list)
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else "",
            "meals": meals_list,
            "total_calories": round(total_cal, 1),
            "total_protein": round(total_pro, 1),
            "total_fat": round(total_fat, 1),
            "total_carbs": round(total_carb, 1),
        }


class MealModel(Base):
    __tablename__ = "meals"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nutrition_day_id = Column(String(36), ForeignKey("nutrition_days.id", ondelete="CASCADE"), nullable=False)
    meal_type = Column(String(20), nullable=False)
    order = Column(Integer, nullable=False, default=0)

    nutrition_day = relationship("NutritionDayModel", back_populates="meals")
    food_items = relationship("FoodItemModel", back_populates="meal", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        foods = [f.to_dict() for f in self.food_items]
        return {
            "id": self.id,
            "meal_type": self.meal_type,
            "food_items": foods,
            "total_calories": round(sum(f["actual_calories"] for f in foods), 1),
            "total_protein": round(sum(f["actual_protein"] for f in foods), 1),
            "total_fat": round(sum(f["actual_fat"] for f in foods), 1),
            "total_carbs": round(sum(f["actual_carbs"] for f in foods), 1),
        }


class FoodItemModel(Base):
    __tablename__ = "food_items"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meal_id = Column(String(36), ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    weight_grams = Column(Float, nullable=False)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)

    meal = relationship("MealModel", back_populates="food_items")

    def to_dict(self) -> dict:
        w = self.weight_grams / 100
        return {
            "id": self.id,
            "name": self.name,
            "weight_grams": self.weight_grams,
            "calories_per_100g": self.calories_per_100g,
            "protein_per_100g": self.protein_per_100g,
            "fat_per_100g": self.fat_per_100g,
            "carbs_per_100g": self.carbs_per_100g,
            "actual_calories": round(self.calories_per_100g * w, 1),
            "actual_protein": round(self.protein_per_100g * w, 1),
            "actual_fat": round(self.fat_per_100g * w, 1),
            "actual_carbs": round(self.carbs_per_100g * w, 1),
        }


class ProductModel(Base):
    __tablename__ = "products"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(255), nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "user_id": self.user_id,
        }


# ---------- Реализация хранилища ----------
class PostgresStorage(BaseStorage):
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    # ─── Пользователи ───
    def create_user(self, username: str, password: str) -> Optional[UserModel]:
        session = self._get_session()
        try:
            if session.query(UserModel).filter(UserModel.username == username).first():
                return None  # пользователь уже существует
            user = UserModel(username=username)
            user.set_password(password)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[UserModel]:
        session = self._get_session()
        try:
            return session.query(UserModel).get(user_id)
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[UserModel]:
        session = self._get_session()
        try:
            return session.query(UserModel).filter(UserModel.username == username).first()
        finally:
            session.close()

    # ─── Тренировочные дни (с фильтром по user_id) ───
    def get_all_workout_days(self, user_id: int) -> list[dict]:
        session = self._get_session()
        try:
            days = session.query(WorkoutDayModel).filter(WorkoutDayModel.user_id == user_id)\
                        .order_by(WorkoutDayModel.date.desc()).all()
            return [day.to_dict() for day in days]
        finally:
            session.close()

    def get_workout_day(self, day_id: str, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            return day.to_dict() if day else None
        finally:
            session.close()

    def create_workout_day(self, date: str, name: str, user_id: int, notes: Optional[str] = None) -> dict:
        session = self._get_session()
        try:
            new_day = WorkoutDayModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date_type.fromisoformat(date),
                name=name,
                notes=notes,
            )
            session.add(new_day)
            session.commit()
            session.refresh(new_day)
            return new_day.to_dict()
        finally:
            session.close()

    def update_workout_day(self, day_id: str, date: str, name: str, user_id: int, notes: Optional[str] = None) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if day:
                day.date = date_type.fromisoformat(date)
                day.name = name
                day.notes = notes
                session.commit()
                session.refresh(day)
                return day.to_dict()
            return None
        finally:
            session.close()

    def delete_workout_day(self, day_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if day:
                session.delete(day)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def add_exercise(self, day_id: str, name: str, sets: List[dict], user_id: int, description: Optional[str] = None) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if not day:
                return None
            existing_count = session.query(ExerciseModel)\
                .filter(ExerciseModel.workout_day_id == day_id).count()
            exercise = ExerciseModel(
                id=str(uuid.uuid4()),
                workout_day_id=day_id,
                name=name,
                description=description,
                order=existing_count,
            )
            session.add(exercise)
            session.flush()
            for idx, s in enumerate(sets):
                set_obj = ExerciseSetModel(
                    id=str(uuid.uuid4()),
                    exercise_id=exercise.id,
                    reps=int(s["reps"]),
                    weight=float(s["weight"]) if s.get("weight") is not None else None,
                    rest_time=int(s["rest_time"]) if s.get("rest_time") is not None else None,
                    order=idx,
                )
                session.add(set_obj)
            session.commit()
            session.refresh(exercise)
            return exercise.to_dict()
        finally:
            session.close()

    def update_exercise(self, day_id: str, exercise_id: str, name: str, sets: List[dict], user_id: int, description: Optional[str] = None) -> Optional[dict]:
        session = self._get_session()
        try:
            exercise = session.query(ExerciseModel).join(WorkoutDayModel).filter(
                ExerciseModel.id == exercise_id,
                ExerciseModel.workout_day_id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if not exercise:
                return None
            exercise.name = name
            exercise.description = description
            for old_set in exercise.sets:
                session.delete(old_set)
            for idx, s in enumerate(sets):
                set_obj = ExerciseSetModel(
                    id=str(uuid.uuid4()),
                    exercise_id=exercise.id,
                    reps=int(s["reps"]),
                    weight=float(s["weight"]) if s.get("weight") is not None else None,
                    rest_time=int(s["rest_time"]) if s.get("rest_time") is not None else None,
                    order=idx,
                )
                session.add(set_obj)
            session.commit()
            session.refresh(exercise)
            return exercise.to_dict()
        finally:
            session.close()

    def copy_workout_day(self, day_id: str, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            original = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if not original:
                return None
            new_day = WorkoutDayModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date_type.today(),
                name=original.name,
            )
            session.add(new_day)
            session.flush()
            for ex in original.exercises:
                new_ex = ExerciseModel(
                    id=str(uuid.uuid4()),
                    workout_day_id=new_day.id,
                    name=ex.name,
                    description=ex.description,
                )
                session.add(new_ex)
                session.flush()
                for s in ex.sets:
                    session.add(ExerciseSetModel(
                        id=str(uuid.uuid4()),
                        exercise_id=new_ex.id,
                        reps=s.reps,
                        weight=s.weight,
                        rest_time=s.rest_time,
                        order=s.order,
                    ))
            session.commit()
            session.refresh(new_day)
            return new_day.to_dict()
        finally:
            session.close()

    def reorder_exercises(self, day_id: str, exercise_ids: List[str], user_id: int) -> bool:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id,
            ).first()
            if not day:
                return False
            for idx, ex_id in enumerate(exercise_ids):
                session.query(ExerciseModel).filter(
                    ExerciseModel.id == ex_id,
                    ExerciseModel.workout_day_id == day_id,
                ).update({"order": idx})
            session.commit()
            return True
        finally:
            session.close()

    def get_exercise_names(self, user_id: int) -> List[str]:
        session = self._get_session()
        try:
            rows = (
                session.query(ExerciseModel.name)
                .join(WorkoutDayModel)
                .filter(WorkoutDayModel.user_id == user_id)
                .distinct()
                .order_by(ExerciseModel.name)
                .all()
            )
            return [r.name for r in rows]
        finally:
            session.close()

    def get_exercise_progress(self, user_id: int, exercise_name: str) -> List[dict]:
        session = self._get_session()
        try:
            exercises = (
                session.query(ExerciseModel, WorkoutDayModel.date)
                .join(WorkoutDayModel)
                .filter(
                    WorkoutDayModel.user_id == user_id,
                    ExerciseModel.name == exercise_name,
                )
                .order_by(WorkoutDayModel.date)
                .all()
            )
            result = []
            for ex, day_date in exercises:
                weights = [s.weight for s in ex.sets if s.weight is not None]
                max_weight = max(weights) if weights else None
                total_volume = sum(
                    s.reps * s.weight for s in ex.sets if s.weight is not None
                )
                result.append({
                    "date": day_date.isoformat(),
                    "max_weight": max_weight,
                    "total_volume": round(total_volume, 2),
                    "sets": len(ex.sets),
                    "total_reps": sum(s.reps for s in ex.sets),
                })
            return result
        finally:
            session.close()

    def delete_exercise(self, day_id: str, exercise_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            exercise = session.query(ExerciseModel).join(WorkoutDayModel).filter(
                ExerciseModel.id == exercise_id,
                ExerciseModel.workout_day_id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if exercise:
                session.delete(exercise)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # ─── Шаблоны тренировок ───
    def get_templates(self, user_id: int) -> List[dict]:
        session = self._get_session()
        try:
            templates = session.query(WorkoutTemplateModel)\
                .filter(WorkoutTemplateModel.user_id == user_id)\
                .order_by(WorkoutTemplateModel.name)\
                .all()
            return [t.to_dict() for t in templates]
        finally:
            session.close()

    def create_template(self, user_id: int, name: str, exercises: List[dict]) -> dict:
        session = self._get_session()
        try:
            tmpl = WorkoutTemplateModel(id=str(uuid.uuid4()), user_id=user_id, name=name)
            session.add(tmpl)
            session.flush()
            for ex_idx, ex in enumerate(exercises):
                tex = TemplateExerciseModel(
                    id=str(uuid.uuid4()),
                    template_id=tmpl.id,
                    name=ex["name"],
                    description=ex.get("description"),
                    order=ex_idx,
                )
                session.add(tex)
                session.flush()
                for s_idx, s in enumerate(ex.get("sets", [])):
                    session.add(TemplateSetModel(
                        id=str(uuid.uuid4()),
                        exercise_id=tex.id,
                        reps=int(s["reps"]),
                        weight=float(s["weight"]) if s.get("weight") is not None else None,
                        rest_time=int(s["rest_time"]) if s.get("rest_time") is not None else None,
                        order=s_idx,
                    ))
            session.commit()
            session.refresh(tmpl)
            return tmpl.to_dict()
        finally:
            session.close()

    def delete_template(self, template_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            tmpl = session.query(WorkoutTemplateModel).filter(
                WorkoutTemplateModel.id == template_id,
                WorkoutTemplateModel.user_id == user_id,
            ).first()
            if tmpl:
                session.delete(tmpl)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def create_workout_from_template(self, template_id: str, user_id: int, date: str) -> Optional[dict]:
        session = self._get_session()
        try:
            tmpl = session.query(WorkoutTemplateModel).filter(
                WorkoutTemplateModel.id == template_id,
                WorkoutTemplateModel.user_id == user_id,
            ).first()
            if not tmpl:
                return None
            new_day = WorkoutDayModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date_type.fromisoformat(date),
                name=tmpl.name,
            )
            session.add(new_day)
            session.flush()
            for tex in tmpl.exercises:
                ex = ExerciseModel(
                    id=str(uuid.uuid4()),
                    workout_day_id=new_day.id,
                    name=tex.name,
                    description=tex.description,
                )
                session.add(ex)
                session.flush()
                for ts in tex.sets:
                    session.add(ExerciseSetModel(
                        id=str(uuid.uuid4()),
                        exercise_id=ex.id,
                        reps=ts.reps,
                        weight=ts.weight,
                        rest_time=ts.rest_time,
                        order=ts.order,
                    ))
            session.commit()
            session.refresh(new_day)
            return new_day.to_dict()
        finally:
            session.close()

    # ─── Питание ───
    def get_nutrition_profile(self, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            p = session.query(NutritionProfileModel).filter(
                NutritionProfileModel.user_id == user_id
            ).first()
            return p.to_dict() if p else None
        finally:
            session.close()

    def upsert_nutrition_profile(self, user_id: int, data: dict) -> dict:
        session = self._get_session()
        try:
            p = session.query(NutritionProfileModel).filter(
                NutritionProfileModel.user_id == user_id
            ).first()
            if p:
                p.sex = data["sex"]
                p.weight = float(data["weight"])
                p.height = float(data["height"])
                p.age = int(data["age"])
                p.activity_level = float(data["activity_level"])
                p.goal = data["goal"]
            else:
                p = NutritionProfileModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    sex=data["sex"],
                    weight=float(data["weight"]),
                    height=float(data["height"]),
                    age=int(data["age"]),
                    activity_level=float(data["activity_level"]),
                    goal=data["goal"],
                )
                session.add(p)
            session.commit()
            session.refresh(p)
            return p.to_dict()
        finally:
            session.close()

    def get_nutrition_days(self, user_id: int) -> List[dict]:
        session = self._get_session()
        try:
            days = session.query(NutritionDayModel).filter(
                NutritionDayModel.user_id == user_id
            ).order_by(NutritionDayModel.date.desc()).all()
            return [d.to_dict() for d in days]
        finally:
            session.close()

    def get_or_create_nutrition_day(self, user_id: int, date: str) -> dict:
        session = self._get_session()
        try:
            d = session.query(NutritionDayModel).filter(
                NutritionDayModel.user_id == user_id,
                NutritionDayModel.date == date_type.fromisoformat(date),
            ).first()
            if not d:
                d = NutritionDayModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    date=date_type.fromisoformat(date),
                )
                session.add(d)
                session.commit()
                session.refresh(d)
            return d.to_dict()
        finally:
            session.close()

    def delete_nutrition_day(self, day_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            d = session.query(NutritionDayModel).filter(
                NutritionDayModel.id == day_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if d:
                session.delete(d)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def create_meal(self, day_id: str, meal_type: str, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(NutritionDayModel).filter(
                NutritionDayModel.id == day_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if not day:
                return None
            existing = session.query(MealModel).filter(MealModel.nutrition_day_id == day_id).count()
            meal = MealModel(
                id=str(uuid.uuid4()),
                nutrition_day_id=day_id,
                meal_type=meal_type,
                order=existing,
            )
            session.add(meal)
            session.commit()
            session.refresh(meal)
            return meal.to_dict()
        finally:
            session.close()

    def delete_meal(self, day_id: str, meal_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            meal = session.query(MealModel).join(NutritionDayModel).filter(
                MealModel.id == meal_id,
                MealModel.nutrition_day_id == day_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if meal:
                session.delete(meal)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def add_food_item(self, meal_id: str, data: dict, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            meal = session.query(MealModel).join(NutritionDayModel).filter(
                MealModel.id == meal_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if not meal:
                return None
            item = FoodItemModel(
                id=str(uuid.uuid4()),
                meal_id=meal_id,
                name=data["name"],
                weight_grams=float(data["weight_grams"]),
                calories_per_100g=float(data["calories_per_100g"]),
                protein_per_100g=float(data["protein_per_100g"]),
                fat_per_100g=float(data["fat_per_100g"]),
                carbs_per_100g=float(data["carbs_per_100g"]),
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item.to_dict()
        finally:
            session.close()

    def update_food_item(self, meal_id: str, food_id: str, data: dict, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            item = session.query(FoodItemModel).join(MealModel).join(NutritionDayModel).filter(
                FoodItemModel.id == food_id,
                FoodItemModel.meal_id == meal_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if not item:
                return None
            item.name = data["name"]
            item.weight_grams = float(data["weight_grams"])
            item.calories_per_100g = float(data["calories_per_100g"])
            item.protein_per_100g = float(data["protein_per_100g"])
            item.fat_per_100g = float(data["fat_per_100g"])
            item.carbs_per_100g = float(data["carbs_per_100g"])
            session.commit()
            session.refresh(item)
            return item.to_dict()
        finally:
            session.close()

    def delete_food_item(self, meal_id: str, food_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            item = session.query(FoodItemModel).join(MealModel).join(NutritionDayModel).filter(
                FoodItemModel.id == food_id,
                FoodItemModel.meal_id == meal_id,
                NutritionDayModel.user_id == user_id,
            ).first()
            if item:
                session.delete(item)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # ─── Справочник продуктов ───
    def get_products(self, user_id: int, query: str = "") -> List[dict]:
        session = self._get_session()
        try:
            q = session.query(ProductModel).filter(
                (ProductModel.user_id == None) | (ProductModel.user_id == user_id)
            )
            if query:
                q = q.filter(ProductModel.name.ilike(f"%{query}%"))
            all_products = q.order_by(ProductModel.name).all()
            seen = {}
            for p in all_products:
                key = p.name.lower()
                if key not in seen or p.user_id is not None:
                    seen[key] = p
            return [p.to_dict() for p in sorted(seen.values(), key=lambda x: x.name)]
        finally:
            session.close()

    def add_product(self, user_id: int, data: dict) -> dict:
        session = self._get_session()
        try:
            p = ProductModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=data["name"],
                calories=float(data["calories"]),
                protein=float(data["protein"]),
                fat=float(data["fat"]),
                carbs=float(data["carbs"]),
            )
            session.add(p)
            session.commit()
            session.refresh(p)
            return p.to_dict()
        finally:
            session.close()

    def add_product_if_not_exists(self, user_id: int, data: dict) -> None:
        session = self._get_session()
        try:
            exists = session.query(ProductModel).filter(
                ProductModel.name.ilike(data["name"]),
                (ProductModel.user_id == None) | (ProductModel.user_id == user_id),
            ).first()
            if not exists:
                session.add(ProductModel(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    name=data["name"],
                    calories=float(data["calories"]),
                    protein=float(data["protein"]),
                    fat=float(data["fat"]),
                    carbs=float(data["carbs"]),
                ))
                session.commit()
        finally:
            session.close()

    def delete_product(self, product_id: str, user_id: int) -> bool:
        session = self._get_session()
        try:
            p = session.query(ProductModel).filter(
                ProductModel.id == product_id,
            ).first()
            if p:
                session.delete(p)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def seed_products_from_json(self, json_path: str) -> None:
        import json as _json
        session = self._get_session()
        try:
            existing = session.query(ProductModel).filter(ProductModel.user_id == None).count()
            if existing > 0:
                return
            with open(json_path, 'r', encoding='utf-8') as f:
                products = _json.load(f)
            for p in products:
                session.add(ProductModel(
                    id=str(uuid.uuid4()),
                    user_id=None,
                    name=p["name"],
                    calories=float(p["calories"]),
                    protein=float(p["protein"]),
                    fat=float(p["fat"]),
                    carbs=float(p["carbs"]),
                ))
            session.commit()
        finally:
            session.close()