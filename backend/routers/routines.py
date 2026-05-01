from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.crud import routine as routine_crud
from backend.schemas.routine import RoutineCreate, RoutineUpdate

router = APIRouter(prefix="/routines", tags=["routines"])


def _format_routine(r) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "goal": r.goal,
        "frequency_per_week": r.frequency_per_week,
        "is_active": r.is_active,
        "source": r.source,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "days": [
            {
                "id": d.id,
                "day_number": d.day_number,
                "name": d.name,
                "day_of_week": d.day_of_week,
                "exercises": [
                    {
                        "id": re.id,
                        "exercise_id": re.exercise_id,
                        "exercise_name": re.exercise.name if re.exercise else "",
                        "order_index": re.order_index,
                        "target_sets": re.target_sets,
                        "target_reps_min": re.target_reps_min,
                        "target_reps_max": re.target_reps_max,
                        "target_weight_kg": re.target_weight_kg,
                        "target_rpe": re.target_rpe,
                        "rest_seconds": re.rest_seconds,
                        "notes": re.notes,
                    }
                    for re in sorted(d.exercises, key=lambda x: x.order_index)
                ],
            }
            for d in sorted(r.days, key=lambda x: x.day_number)
        ],
    }


@router.get("")
def list_routines(db: Session = Depends(get_db)):
    routines = routine_crud.get_routines(db)
    return [_format_routine(r) for r in routines]


@router.post("")
def create_routine(data: RoutineCreate, db: Session = Depends(get_db)):
    routine_data = data.model_dump()
    routine = routine_crud.create_routine(db, routine_data)
    return _format_routine(routine)


@router.get("/{routine_id}")
def get_routine(routine_id: int, db: Session = Depends(get_db)):
    routine = routine_crud.get_routine(db, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
    return _format_routine(routine)


@router.put("/{routine_id}")
def update_routine(routine_id: int, data: RoutineUpdate, db: Session = Depends(get_db)):
    routine = routine_crud.update_routine(db, routine_id, data.model_dump(exclude_none=True))
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
    return _format_routine(routine)


@router.delete("/{routine_id}")
def delete_routine(routine_id: int, db: Session = Depends(get_db)):
    deleted = routine_crud.delete_routine(db, routine_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"deleted": True}


@router.post("/{routine_id}/activate")
def activate_routine(routine_id: int, db: Session = Depends(get_db)):
    routine = routine_crud.activate_routine(db, routine_id)
    if not routine:
        raise HTTPException(status_code=404, detail="Routine not found")
    return {"active_routine_id": routine.id}
