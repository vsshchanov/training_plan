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

    user = relationship("UserModel", back_populates="workout_days")
    exercises = relationship("ExerciseModel", back_populates="workout_day", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else "",
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises],
        }


class ExerciseModel(Base):
    __tablename__ = "exercises"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workout_day_id = Column(String(36), ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

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

    def create_workout_day(self, date: str, name: str, user_id: int) -> dict:
        session = self._get_session()
        try:
            new_day = WorkoutDayModel(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date_type.fromisoformat(date),
                name=name,
            )
            session.add(new_day)
            session.commit()
            session.refresh(new_day)
            return new_day.to_dict()
        finally:
            session.close()

    def update_workout_day(self, day_id: str, date: str, name: str, user_id: int) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if day:
                day.date = date_type.fromisoformat(date)
                day.name = name
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

    def add_exercise(self, day_id: str, name: str, sets: List[dict], user_id: int, description: str = None) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(
                WorkoutDayModel.id == day_id,
                WorkoutDayModel.user_id == user_id
            ).first()
            if not day:
                return None
            exercise = ExerciseModel(
                id=str(uuid.uuid4()),
                workout_day_id=day_id,
                name=name,
                description=description,
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

    def update_exercise(self, day_id: str, exercise_id: str, name: str, sets: List[dict], user_id: int, description: str = None) -> Optional[dict]:
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