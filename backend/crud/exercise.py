from sqlalchemy.orm import Session

from backend.models.exercise import ExerciseDefinition


def get_exercises(db: Session, search: str = "", category: str = "", muscle_group: str = "") -> list[ExerciseDefinition]:
    q = db.query(ExerciseDefinition)
    if search:
        q = q.filter(ExerciseDefinition.name.ilike(f"%{search}%"))
    if category:
        q = q.filter(ExerciseDefinition.category == category)
    if muscle_group:
        q = q.filter(ExerciseDefinition.muscle_groups_primary.ilike(f"%{muscle_group}%"))
    return q.order_by(ExerciseDefinition.name).all()


def get_exercise(db: Session, exercise_id: int) -> ExerciseDefinition | None:
    return db.query(ExerciseDefinition).filter(ExerciseDefinition.id == exercise_id).first()


def find_or_create_exercise(db: Session, name: str) -> ExerciseDefinition:
    """Fuzzy-match by name; create custom if not found."""
    exercise = db.query(ExerciseDefinition).filter(
        ExerciseDefinition.name.ilike(name)
    ).first()
    if not exercise:
        # Try partial match
        exercise = db.query(ExerciseDefinition).filter(
            ExerciseDefinition.name.ilike(f"%{name}%")
        ).first()
    if not exercise:
        exercise = ExerciseDefinition(name=name, is_custom=True)
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
    return exercise


def create_exercise(db: Session, data: dict) -> ExerciseDefinition:
    exercise = ExerciseDefinition(**data)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise
