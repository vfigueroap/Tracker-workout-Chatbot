from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services import progress_service

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    return progress_service.get_dashboard_snapshot(db)


@router.get("/exercise/{exercise_id}")
def exercise_progress(
    exercise_id: int,
    days: int = Query(90, ge=7, le=365),
    db: Session = Depends(get_db),
):
    return progress_service.get_exercise_progress(db, exercise_id, days)


@router.get("/volume")
def volume_over_time(
    days: int = Query(56, ge=7, le=365),
    group_by: str = Query("week"),
    db: Session = Depends(get_db),
):
    return progress_service.get_volume_over_time(db, days, group_by)


@router.get("/muscle-groups")
def muscle_group_breakdown(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
):
    return progress_service.get_muscle_group_breakdown(db, days)
