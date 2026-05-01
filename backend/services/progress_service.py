import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.models.session import WorkoutSession, SessionExercise, ExerciseSet
from backend.models.exercise import ExerciseDefinition
from backend.crud.session import get_recent_sessions


def get_dashboard_snapshot(db: Session) -> dict:
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    recent = db.query(WorkoutSession).filter(
        WorkoutSession.status == "completed",
        WorkoutSession.started_at >= thirty_days_ago,
    ).order_by(WorkoutSession.started_at.desc()).all()

    total_sessions = db.query(WorkoutSession).filter(WorkoutSession.status == "completed").count()
    total_volume_month = sum(s.total_volume_kg for s in recent)

    # Current streak
    streak = _compute_streak(db)

    # Last workout date
    last_session = db.query(WorkoutSession).filter(
        WorkoutSession.status == "completed"
    ).order_by(WorkoutSession.started_at.desc()).first()
    last_workout_date = last_session.started_at.date().isoformat() if last_session else None

    return {
        "streak_days": streak,
        "sessions_this_month": len(recent),
        "total_sessions": total_sessions,
        "volume_this_month_kg": round(total_volume_month, 1),
        "last_workout_date": last_workout_date,
        "recent_sessions": [
            {
                "id": s.id,
                "date": s.started_at.date().isoformat(),
                "duration_min": _duration_min(s),
                "routine_day_name": s.routine_day.name if s.routine_day else "Free Workout",
                "total_volume_kg": s.total_volume_kg,
                "overall_feeling": s.overall_feeling,
            }
            for s in recent[:5]
        ],
    }


def get_exercise_progress(db: Session, exercise_id: int, days: int = 90) -> dict:
    exercise = db.query(ExerciseDefinition).filter(ExerciseDefinition.id == exercise_id).first()
    if not exercise:
        return {"error": "Exercise not found"}

    cutoff = datetime.utcnow() - timedelta(days=days)
    session_exercises = (
        db.query(SessionExercise)
        .join(WorkoutSession)
        .filter(
            SessionExercise.exercise_id == exercise_id,
            WorkoutSession.status == "completed",
            WorkoutSession.started_at >= cutoff,
        )
        .order_by(WorkoutSession.started_at.asc())
        .all()
    )

    history = []
    personal_best = {"weight_kg": 0.0, "reps": 0, "date": None}

    for se in session_exercises:
        session_date = se.session.started_at.date().isoformat()
        working_sets = [s for s in se.sets if not s.is_warmup and s.weight_kg is not None]
        if not working_sets:
            continue

        max_weight = max((s.weight_kg for s in working_sets), default=0)
        total_volume = sum((s.weight_kg or 0) * (s.reps or 0) for s in working_sets)
        best_set = max(working_sets, key=lambda s: (s.weight_kg or 0))

        history.append({
            "date": session_date,
            "max_weight_kg": max_weight,
            "total_volume_kg": round(total_volume, 1),
            "best_set": {"reps": best_set.reps, "weight_kg": best_set.weight_kg},
        })

        if max_weight > personal_best["weight_kg"]:
            personal_best = {"weight_kg": max_weight, "reps": best_set.reps, "date": session_date}

    trend = _compute_trend([h["max_weight_kg"] for h in history])

    return {
        "exercise": {"id": exercise.id, "name": exercise.name},
        "history": history,
        "personal_best": personal_best,
        "trend": trend,
    }


def get_volume_over_time(db: Session, days: int = 56, group_by: str = "week") -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.status == "completed", WorkoutSession.started_at >= cutoff)
        .order_by(WorkoutSession.started_at.asc())
        .all()
    )

    buckets: dict[str, dict] = {}
    for s in sessions:
        if group_by == "week":
            dt = s.started_at.date()
            monday = dt - timedelta(days=dt.weekday())
            key = monday.isoformat()
        else:
            key = s.started_at.date().isoformat()

        if key not in buckets:
            buckets[key] = {"period": key, "total_volume_kg": 0.0, "session_count": 0}
        buckets[key]["total_volume_kg"] = round(buckets[key]["total_volume_kg"] + s.total_volume_kg, 1)
        buckets[key]["session_count"] += 1

    return list(buckets.values())


def get_muscle_group_breakdown(db: Session, days: int = 30) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    session_exercises = (
        db.query(SessionExercise)
        .join(WorkoutSession)
        .filter(
            WorkoutSession.status == "completed",
            WorkoutSession.started_at >= cutoff,
        )
        .all()
    )

    breakdown: dict[str, dict] = {}
    for se in session_exercises:
        muscle_groups = json.loads(se.exercise.muscle_groups_primary or "[]")
        volume = sum((s.weight_kg or 0) * (s.reps or 0) for s in se.sets if not s.is_warmup)
        for mg in muscle_groups:
            if mg not in breakdown:
                breakdown[mg] = {"muscle_group": mg, "volume_kg": 0.0, "session_count": 0}
            breakdown[mg]["volume_kg"] = round(breakdown[mg]["volume_kg"] + volume, 1)
            breakdown[mg]["session_count"] += 1

    return sorted(breakdown.values(), key=lambda x: x["volume_kg"], reverse=True)


def _duration_min(session: WorkoutSession) -> int | None:
    if session.ended_at and session.started_at:
        delta = session.ended_at - session.started_at
        return int(delta.total_seconds() / 60)
    return None


def _compute_streak(db: Session) -> int:
    sessions = (
        db.query(WorkoutSession)
        .filter(WorkoutSession.status == "completed")
        .order_by(WorkoutSession.started_at.desc())
        .all()
    )
    if not sessions:
        return 0

    streak = 0
    today = datetime.utcnow().date()
    checked_date = today

    seen_dates = {s.started_at.date() for s in sessions}

    for _ in range(365):
        if checked_date in seen_dates:
            streak += 1
            checked_date -= timedelta(days=1)
        elif checked_date == today:
            checked_date -= timedelta(days=1)
        else:
            break

    return streak


def _compute_trend(values: list[float]) -> str:
    if len(values) < 3:
        return "insufficient_data"
    first_half = sum(values[: len(values) // 2]) / (len(values) // 2)
    second_half = sum(values[len(values) // 2 :]) / (len(values) - len(values) // 2)
    diff_pct = (second_half - first_half) / max(first_half, 1) * 100
    if diff_pct > 3:
        return "improving"
    if diff_pct < -3:
        return "declining"
    return "plateau"


def get_top_exercises_with_prs(db: Session, limit: int = 10) -> list[dict]:
    """Get the user's top exercises by frequency with their PRs — used in system prompt."""
    from sqlalchemy import func
    results = (
        db.query(
            SessionExercise.exercise_id,
            ExerciseDefinition.name,
            func.count(SessionExercise.id).label("frequency"),
        )
        .join(ExerciseDefinition, SessionExercise.exercise_id == ExerciseDefinition.id)
        .join(WorkoutSession, SessionExercise.session_id == WorkoutSession.id)
        .filter(WorkoutSession.status == "completed")
        .group_by(SessionExercise.exercise_id)
        .order_by(func.count(SessionExercise.id).desc())
        .limit(limit)
        .all()
    )

    top = []
    for exercise_id, exercise_name, freq in results:
        sets = (
            db.query(ExerciseSet)
            .join(SessionExercise)
            .join(WorkoutSession)
            .filter(
                SessionExercise.exercise_id == exercise_id,
                WorkoutSession.status == "completed",
                ExerciseSet.is_warmup == False,  # noqa: E712
                ExerciseSet.weight_kg.isnot(None),
            )
            .order_by(ExerciseSet.weight_kg.desc())
            .first()
        )
        top.append({
            "name": exercise_name,
            "pr_weight_kg": sets.weight_kg if sets else None,
            "pr_reps": sets.reps if sets else None,
        })

    return top
