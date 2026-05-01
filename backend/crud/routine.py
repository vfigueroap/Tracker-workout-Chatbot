import json
from sqlalchemy.orm import Session

from backend.models.routine import Routine, RoutineDay, RoutineExercise
from backend.crud.exercise import find_or_create_exercise


def get_routines(db: Session) -> list[Routine]:
    return db.query(Routine).order_by(Routine.created_at.desc()).all()


def get_routine(db: Session, routine_id: int) -> Routine | None:
    return db.query(Routine).filter(Routine.id == routine_id).first()


def get_active_routine(db: Session) -> Routine | None:
    return db.query(Routine).filter(Routine.is_active == True).first()  # noqa: E712


def create_routine(db: Session, data: dict) -> Routine:
    days_data = data.pop("days", [])
    routine = Routine(**data)
    db.add(routine)
    db.flush()

    for day_d in days_data:
        exercises_data = day_d.pop("exercises", [])
        day = RoutineDay(routine_id=routine.id, **day_d)
        db.add(day)
        db.flush()

        for order, ex_d in enumerate(exercises_data):
            exercise_name = ex_d.pop("exercise_name")
            exercise = find_or_create_exercise(db, exercise_name)
            re = RoutineExercise(
                routine_day_id=day.id,
                exercise_id=exercise.id,
                order_index=ex_d.pop("order_index", order),
                **ex_d,
            )
            db.add(re)

    db.commit()
    db.refresh(routine)
    return routine


def update_routine(db: Session, routine_id: int, data: dict) -> Routine | None:
    routine = get_routine(db, routine_id)
    if not routine:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(routine, key, value)
    db.commit()
    db.refresh(routine)
    return routine


def activate_routine(db: Session, routine_id: int) -> Routine | None:
    db.query(Routine).update({"is_active": False})
    routine = get_routine(db, routine_id)
    if not routine:
        return None
    routine.is_active = True
    db.commit()
    db.refresh(routine)
    return routine


def delete_routine(db: Session, routine_id: int) -> bool:
    routine = get_routine(db, routine_id)
    if not routine:
        return False
    db.delete(routine)
    db.commit()
    return True
