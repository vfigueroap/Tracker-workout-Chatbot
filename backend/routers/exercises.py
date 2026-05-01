from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import exercise as exercise_crud

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("")
def list_exercises(
    search: str = Query(""),
    category: str = Query(""),
    muscle_group: str = Query(""),
    db: Session = Depends(get_db),
):
    exercises = exercise_crud.get_exercises(db, search=search, category=category, muscle_group=muscle_group)
    return [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category,
            "muscle_groups_primary": e.muscle_groups_primary,
            "muscle_groups_secondary": e.muscle_groups_secondary,
            "equipment": e.equipment,
            "is_custom": e.is_custom,
        }
        for e in exercises
    ]
