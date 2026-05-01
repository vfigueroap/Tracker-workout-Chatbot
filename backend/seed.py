"""Seed the database with common exercises and a default user profile."""
import json
from sqlalchemy.orm import Session

from backend.models.exercise import ExerciseDefinition
from backend.models.user import UserProfile


EXERCISES = [
    # Chest
    {"name": "Barbell Bench Press", "category": "strength", "muscle_groups_primary": ["chest"], "muscle_groups_secondary": ["triceps", "front delts"], "equipment": "barbell"},
    {"name": "Incline Barbell Bench Press", "category": "strength", "muscle_groups_primary": ["upper chest"], "muscle_groups_secondary": ["triceps", "front delts"], "equipment": "barbell"},
    {"name": "Dumbbell Bench Press", "category": "strength", "muscle_groups_primary": ["chest"], "muscle_groups_secondary": ["triceps", "front delts"], "equipment": "dumbbell"},
    {"name": "Incline Dumbbell Press", "category": "strength", "muscle_groups_primary": ["upper chest"], "muscle_groups_secondary": ["triceps", "front delts"], "equipment": "dumbbell"},
    {"name": "Dumbbell Fly", "category": "strength", "muscle_groups_primary": ["chest"], "muscle_groups_secondary": ["front delts"], "equipment": "dumbbell"},
    {"name": "Cable Fly", "category": "strength", "muscle_groups_primary": ["chest"], "muscle_groups_secondary": ["front delts"], "equipment": "cable"},
    {"name": "Push-up", "category": "strength", "muscle_groups_primary": ["chest"], "muscle_groups_secondary": ["triceps", "front delts"], "equipment": "bodyweight"},
    # Back
    {"name": "Barbell Row", "category": "strength", "muscle_groups_primary": ["lats", "rhomboids"], "muscle_groups_secondary": ["biceps", "rear delts"], "equipment": "barbell"},
    {"name": "Deadlift", "category": "strength", "muscle_groups_primary": ["hamstrings", "glutes", "lower back"], "muscle_groups_secondary": ["traps", "lats", "core"], "equipment": "barbell"},
    {"name": "Romanian Deadlift", "category": "strength", "muscle_groups_primary": ["hamstrings", "glutes"], "muscle_groups_secondary": ["lower back"], "equipment": "barbell"},
    {"name": "Pull-up", "category": "strength", "muscle_groups_primary": ["lats"], "muscle_groups_secondary": ["biceps", "rear delts"], "equipment": "bodyweight"},
    {"name": "Lat Pulldown", "category": "strength", "muscle_groups_primary": ["lats"], "muscle_groups_secondary": ["biceps", "rear delts"], "equipment": "cable"},
    {"name": "Seated Cable Row", "category": "strength", "muscle_groups_primary": ["lats", "rhomboids"], "muscle_groups_secondary": ["biceps", "rear delts"], "equipment": "cable"},
    {"name": "Dumbbell Row", "category": "strength", "muscle_groups_primary": ["lats", "rhomboids"], "muscle_groups_secondary": ["biceps"], "equipment": "dumbbell"},
    {"name": "Face Pull", "category": "strength", "muscle_groups_primary": ["rear delts", "rotator cuff"], "muscle_groups_secondary": ["traps"], "equipment": "cable"},
    # Shoulders
    {"name": "Overhead Press", "category": "strength", "muscle_groups_primary": ["front delts", "side delts"], "muscle_groups_secondary": ["triceps", "traps"], "equipment": "barbell"},
    {"name": "Dumbbell Shoulder Press", "category": "strength", "muscle_groups_primary": ["front delts", "side delts"], "muscle_groups_secondary": ["triceps"], "equipment": "dumbbell"},
    {"name": "Lateral Raise", "category": "strength", "muscle_groups_primary": ["side delts"], "muscle_groups_secondary": [], "equipment": "dumbbell"},
    {"name": "Front Raise", "category": "strength", "muscle_groups_primary": ["front delts"], "muscle_groups_secondary": [], "equipment": "dumbbell"},
    {"name": "Rear Delt Fly", "category": "strength", "muscle_groups_primary": ["rear delts"], "muscle_groups_secondary": ["rhomboids"], "equipment": "dumbbell"},
    # Legs
    {"name": "Barbell Back Squat", "category": "strength", "muscle_groups_primary": ["quads", "glutes"], "muscle_groups_secondary": ["hamstrings", "core"], "equipment": "barbell"},
    {"name": "Barbell Front Squat", "category": "strength", "muscle_groups_primary": ["quads"], "muscle_groups_secondary": ["glutes", "core"], "equipment": "barbell"},
    {"name": "Leg Press", "category": "strength", "muscle_groups_primary": ["quads", "glutes"], "muscle_groups_secondary": ["hamstrings"], "equipment": "machine"},
    {"name": "Leg Extension", "category": "strength", "muscle_groups_primary": ["quads"], "muscle_groups_secondary": [], "equipment": "machine"},
    {"name": "Leg Curl", "category": "strength", "muscle_groups_primary": ["hamstrings"], "muscle_groups_secondary": [], "equipment": "machine"},
    {"name": "Bulgarian Split Squat", "category": "strength", "muscle_groups_primary": ["quads", "glutes"], "muscle_groups_secondary": ["hamstrings", "core"], "equipment": "dumbbell"},
    {"name": "Lunge", "category": "strength", "muscle_groups_primary": ["quads", "glutes"], "muscle_groups_secondary": ["hamstrings"], "equipment": "bodyweight"},
    {"name": "Hip Thrust", "category": "strength", "muscle_groups_primary": ["glutes"], "muscle_groups_secondary": ["hamstrings"], "equipment": "barbell"},
    {"name": "Calf Raise", "category": "strength", "muscle_groups_primary": ["calves"], "muscle_groups_secondary": [], "equipment": "machine"},
    {"name": "Goblet Squat", "category": "strength", "muscle_groups_primary": ["quads", "glutes"], "muscle_groups_secondary": ["core"], "equipment": "dumbbell"},
    # Arms - Biceps
    {"name": "Barbell Curl", "category": "strength", "muscle_groups_primary": ["biceps"], "muscle_groups_secondary": ["brachialis"], "equipment": "barbell"},
    {"name": "Dumbbell Curl", "category": "strength", "muscle_groups_primary": ["biceps"], "muscle_groups_secondary": ["brachialis"], "equipment": "dumbbell"},
    {"name": "Hammer Curl", "category": "strength", "muscle_groups_primary": ["brachialis", "brachioradialis"], "muscle_groups_secondary": ["biceps"], "equipment": "dumbbell"},
    {"name": "Cable Curl", "category": "strength", "muscle_groups_primary": ["biceps"], "muscle_groups_secondary": [], "equipment": "cable"},
    {"name": "Preacher Curl", "category": "strength", "muscle_groups_primary": ["biceps"], "muscle_groups_secondary": [], "equipment": "barbell"},
    # Arms - Triceps
    {"name": "Close-Grip Bench Press", "category": "strength", "muscle_groups_primary": ["triceps"], "muscle_groups_secondary": ["chest"], "equipment": "barbell"},
    {"name": "Tricep Pushdown", "category": "strength", "muscle_groups_primary": ["triceps"], "muscle_groups_secondary": [], "equipment": "cable"},
    {"name": "Overhead Tricep Extension", "category": "strength", "muscle_groups_primary": ["triceps"], "muscle_groups_secondary": [], "equipment": "dumbbell"},
    {"name": "Skullcrusher", "category": "strength", "muscle_groups_primary": ["triceps"], "muscle_groups_secondary": [], "equipment": "barbell"},
    {"name": "Dip", "category": "strength", "muscle_groups_primary": ["triceps", "chest"], "muscle_groups_secondary": ["front delts"], "equipment": "bodyweight"},
    # Core
    {"name": "Plank", "category": "strength", "muscle_groups_primary": ["core"], "muscle_groups_secondary": ["shoulders"], "equipment": "bodyweight"},
    {"name": "Ab Crunch", "category": "strength", "muscle_groups_primary": ["abs"], "muscle_groups_secondary": [], "equipment": "bodyweight"},
    {"name": "Leg Raise", "category": "strength", "muscle_groups_primary": ["lower abs"], "muscle_groups_secondary": ["hip flexors"], "equipment": "bodyweight"},
    {"name": "Russian Twist", "category": "strength", "muscle_groups_primary": ["obliques"], "muscle_groups_secondary": ["abs"], "equipment": "bodyweight"},
    {"name": "Cable Crunch", "category": "strength", "muscle_groups_primary": ["abs"], "muscle_groups_secondary": [], "equipment": "cable"},
    # Cardio
    {"name": "Treadmill Run", "category": "cardio", "muscle_groups_primary": ["cardiovascular"], "muscle_groups_secondary": ["legs"], "equipment": "machine"},
    {"name": "Stationary Bike", "category": "cardio", "muscle_groups_primary": ["cardiovascular"], "muscle_groups_secondary": ["quads"], "equipment": "machine"},
    {"name": "Rowing Machine", "category": "cardio", "muscle_groups_primary": ["cardiovascular", "back"], "muscle_groups_secondary": ["legs", "arms"], "equipment": "machine"},
    {"name": "Jump Rope", "category": "cardio", "muscle_groups_primary": ["cardiovascular"], "muscle_groups_secondary": ["calves"], "equipment": "other"},
]


def seed_exercises(db: Session) -> None:
    existing = db.query(ExerciseDefinition).count()
    if existing > 0:
        return
    for ex in EXERCISES:
        exercise = ExerciseDefinition(
            name=ex["name"],
            category=ex["category"],
            muscle_groups_primary=json.dumps(ex["muscle_groups_primary"]),
            muscle_groups_secondary=json.dumps(ex["muscle_groups_secondary"]),
            equipment=ex["equipment"],
        )
        db.add(exercise)
    db.commit()


def seed_user(db: Session) -> None:
    existing = db.query(UserProfile).first()
    if existing:
        return
    user = UserProfile(
        name="Athlete",
        fitness_level="intermediate",
        primary_goal="build muscle",
        equipment_available=json.dumps(["barbell", "dumbbell", "cable"]),
    )
    db.add(user)
    db.commit()


def run_seed(db: Session) -> None:
    seed_exercises(db)
    seed_user(db)
