"""
Хранилище данных в PostgreSQL с использованием SQLAlchemy.
"""

from typing import Optional, List
from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, Date, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base, Session
import uuid
from datetime import date as date_type

from storage.base import BaseStorage

Base = declarative_base()

class WorkoutDayModel(Base):
    __tablename__ = "workout_days"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    name = Column(String(255), nullable=False)
    exercises = relationship("ExerciseModel", back_populates="workout_day", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else "",
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises],
        }

class ExerciseModel(Base):
    __tablename__ = "exercises"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workout_day_id = Column(String(36), ForeignKey("workout_days.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    workout_day = relationship("WorkoutDayModel", back_populates="exercises")
    sets = relationship("ExerciseSetModel", back_populates="exercise", cascade="all, delete-orphan",
                        order_by="ExerciseSetModel.order")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "sets": [s.to_dict() for s in self.sets],
        }

class ExerciseSetModel(Base):
    __tablename__ = "exercise_sets"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_id = Column(String(36), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    reps = Column(Integer, nullable=False)
    weight = Column(Float, nullable=True)
    rest_time = Column(Integer, nullable=True)  # в секундах
    order = Column(Integer, nullable=False, default=0)
    exercise = relationship("ExerciseModel", back_populates="sets")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reps": self.reps,
            "weight": self.weight,
            "rest_time": self.rest_time,
        }

class PostgresStorage(BaseStorage):
    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def get_all_workout_days(self) -> list[dict]:
        session = self._get_session()
        try:
            days = session.query(WorkoutDayModel).order_by(WorkoutDayModel.date.desc()).all()
            return [day.to_dict() for day in days]
        finally:
            session.close()

    def get_workout_day(self, day_id: str) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(WorkoutDayModel.id == day_id).first()
            return day.to_dict() if day else None
        finally:
            session.close()

    def create_workout_day(self, date: str, name: str) -> dict:
        session = self._get_session()
        try:
            new_day = WorkoutDayModel(
                id=str(uuid.uuid4()),
                date=date_type.fromisoformat(date),
                name=name,
            )
            session.add(new_day)
            session.commit()
            session.refresh(new_day)
            return new_day.to_dict()
        finally:
            session.close()

    def update_workout_day(self, day_id: str, date: str, name: str) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(WorkoutDayModel.id == day_id).first()
            if day:
                day.date = date_type.fromisoformat(date)
                day.name = name
                session.commit()
                session.refresh(day)
                return day.to_dict()
            return None
        finally:
            session.close()

    def delete_workout_day(self, day_id: str) -> bool:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(WorkoutDayModel.id == day_id).first()
            if day:
                session.delete(day)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def add_exercise(self, day_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        session = self._get_session()
        try:
            day = session.query(WorkoutDayModel).filter(WorkoutDayModel.id == day_id).first()
            if not day:
                return None
            exercise = ExerciseModel(
                id=str(uuid.uuid4()),
                workout_day_id=day_id,
                name=name,
            )
            session.add(exercise)
            session.flush()  # чтобы получить exercise.id для сетов
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

    def update_exercise(self, day_id: str, exercise_id: str, name: str, sets: List[dict]) -> Optional[dict]:
        session = self._get_session()
        try:
            exercise = session.query(ExerciseModel).filter(
                ExerciseModel.id == exercise_id,
                ExerciseModel.workout_day_id == day_id,
            ).first()
            if not exercise:
                return None
            exercise.name = name
            # Удаляем старые сеты
            for old_set in exercise.sets:
                session.delete(old_set)
            # Добавляем новые
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

    def delete_exercise(self, day_id: str, exercise_id: str) -> bool:
        session = self._get_session()
        try:
            exercise = session.query(ExerciseModel).filter(
                ExerciseModel.id == exercise_id,
                ExerciseModel.workout_day_id == day_id,
            ).first()
            if exercise:
                session.delete(exercise)
                session.commit()
                return True
            return False
        finally:
            session.close()