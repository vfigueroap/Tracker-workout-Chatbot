from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import session as session_crud
from backend.schemas.session import (
    WorkoutSessionOut, SessionCreate, SessionUpdate, LogExerciseRequest, SessionExerciseOut
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _format_session(s) -> dict:
    return {
        "id": s.id,
        "routine_id": s.routine_id,
        "routine_day_id": s.routine_day_id,
        "routine_day_name": s.routine_day.name if s.routine_day else None,
        "started_at": s.started_at,
        "ended_at": s.ended_at,
        "status": s.status,
        "overall_feeling": s.overall_feeling,
        "notes": s.notes,
        "ai_summary": s.ai_summary,
        "total_volume_kg": s.total_volume_kg,
        "exercises": [
            {
                "id": se.id,
                "exercise_id": se.exercise_id,
                "exercise_name": se.exercise.name if se.exercise else "",
                "order_performed": se.order_performed,
                "notes": se.notes,
                "sets": [
                    {
                        "id": st.id,
                        "set_number": st.set_number,
                        "reps": st.reps,
                        "weight_kg": st.weight_kg,
                        "duration_seconds": st.duration_seconds,
                        "rpe": st.rpe,
                        "is_warmup": st.is_warmup,
                        "logged_at": st.logged_at,
                    }
                    for st in se.sets
                ],
            }
            for se in s.exercises
        ],
    }


@router.get("")
def list_sessions(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str = Query(""),
    db: Session = Depends(get_db),
):
    sessions, total = session_crud.get_sessions(db, limit=limit, offset=offset, status=status)
    return {"sessions": [_format_session(s) for s in sessions], "total": total}


@router.post("")
def create_session(data: SessionCreate, db: Session = Depends(get_db)):
    session = session_crud.create_session(db, data.model_dump(exclude_none=True))
    return _format_session(session)


@router.get("/active")
def get_active_session(db: Session = Depends(get_db)):
    session = session_crud.get_active_session(db)
    if not session:
        return None
    return _format_session(session)


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = session_crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _format_session(session)


@router.put("/{session_id}")
def update_session(session_id: int, data: SessionUpdate, db: Session = Depends(get_db)):
    session = session_crud.update_session(db, session_id, data.model_dump(exclude_none=True))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _format_session(session)


@router.post("/{session_id}/exercises")
def log_exercise(session_id: int, data: LogExerciseRequest, db: Session = Depends(get_db)):
    session = session_crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    exercise_name = data.exercise_name or ""
    if not exercise_name and data.exercise_id:
        from backend.crud.exercise import get_exercise
        ex = get_exercise(db, data.exercise_id)
        exercise_name = ex.name if ex else "Unknown"

    sets_data = [s.model_dump() for s in data.sets]
    se = session_crud.log_exercise_to_session(db, session_id, exercise_name, sets_data, data.notes or "")
    return {
        "id": se.id,
        "exercise_id": se.exercise_id,
        "exercise_name": se.exercise.name,
        "sets": [{"id": st.id, "set_number": st.set_number, "reps": st.reps, "weight_kg": st.weight_kg} for st in se.sets],
    }
