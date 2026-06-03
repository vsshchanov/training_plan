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