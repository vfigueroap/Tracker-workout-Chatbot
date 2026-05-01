from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.session import WorkoutSession, SessionExercise, ExerciseSet
from backend.crud.exercise import find_or_create_exercise


def get_sessions(db: Session, limit: int = 20, offset: int = 0, status: str = "") -> tuple[list[WorkoutSession], int]:
    q = db.query(WorkoutSession)
    if status:
        q = q.filter(WorkoutSession.status == status)
    total = q.count()
    sessions = q.order_by(WorkoutSession.started_at.desc()).offset(offset).limit(limit).all()
    return sessions, total


def get_session(db: Session, session_id: int) -> WorkoutSession | None:
    return db.query(WorkoutSession).filter(WorkoutSession.id == session_id).first()


def get_active_session(db: Session) -> WorkoutSession | None:
    return db.query(WorkoutSession).filter(WorkoutSession.status == "in_progress").first()


def create_session(db: Session, data: dict) -> WorkoutSession:
    session = WorkoutSession(**data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def update_session(db: Session, session_id: int, data: dict) -> WorkoutSession | None:
    session = get_session(db, session_id)
    if not session:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(session, key, value)
    if data.get("status") in ("completed", "abandoned") and not session.ended_at:
        session.ended_at = datetime.utcnow()
        session.total_volume_kg = _compute_volume(db, session_id)
    db.commit()
    db.refresh(session)
    return session


def _compute_volume(db: Session, session_id: int) -> float:
    total = 0.0
    session_exercises = db.query(SessionExercise).filter(SessionExercise.session_id == session_id).all()
    for se in session_exercises:
        for s in se.sets:
            if not s.is_warmup and s.weight_kg and s.reps:
                total += s.weight_kg * s.reps
    return total


def log_exercise_to_session(db: Session, session_id: int, exercise_name: str, sets_data: list[dict], notes: str = "") -> SessionExercise:
    exercise = find_or_create_exercise(db, exercise_name)

    count = db.query(SessionExercise).filter(SessionExercise.session_id == session_id).count()
    se = SessionExercise(
        session_id=session_id,
        exercise_id=exercise.id,
        order_performed=count,
        notes=notes or None,
    )
    db.add(se)
    db.flush()

    for set_d in sets_data:
        es = ExerciseSet(session_exercise_id=se.id, **set_d)
        db.add(es)

    db.commit()
    db.refresh(se)
    return se


def get_recent_sessions(db: Session, limit: int = 4) -> list[WorkoutSession]:
    return (
        db.query(WorkoutSession)
        .filter(WorkoutSession.status == "completed")
        .order_by(WorkoutSession.started_at.desc())
        .limit(limit)
        .all()
    )
