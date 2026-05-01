"""Executes Claude tool calls against the database."""
import json
from sqlalchemy.orm import Session

from backend.crud import session as session_crud
from backend.crud import routine as routine_crud
from backend.crud import user as user_crud
from backend.services.progress_service import get_exercise_progress
from backend.crud.exercise import find_or_create_exercise


def handle_tool(db: Session, tool_name: str, tool_input: dict, current_session_id: int | None) -> tuple[dict, int | None]:
    """Dispatch a tool call. Returns (result_dict, updated_session_id)."""
    handlers = {
        "start_workout_session": _start_session,
        "end_workout_session": _end_session,
        "log_exercise": _log_exercise,
        "create_or_update_routine": _create_or_update_routine,
        "update_user_profile": _update_user_profile,
        "get_exercise_progress": _get_exercise_progress,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}, current_session_id

    return handler(db, tool_input, current_session_id)


def _start_session(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    data = {}
    if inp.get("routine_id"):
        data["routine_id"] = inp["routine_id"]
    if inp.get("routine_day_id"):
        data["routine_day_id"] = inp["routine_day_id"]
    if inp.get("notes"):
        data["notes"] = inp["notes"]
    session = session_crud.create_session(db, data)
    return {
        "success": True,
        "session_id": session.id,
        "message": f"Session #{session.id} started.",
    }, session.id


def _end_session(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    sid = inp.get("session_id") or session_id
    if not sid:
        return {"error": "No session_id provided or active."}, None

    update_data = {"status": inp.get("status", "completed")}
    if inp.get("overall_feeling"):
        update_data["overall_feeling"] = inp["overall_feeling"]
    if inp.get("notes"):
        update_data["notes"] = inp["notes"]

    session = session_crud.update_session(db, sid, update_data)
    if not session:
        return {"error": f"Session {sid} not found."}, None

    return {
        "success": True,
        "session_id": sid,
        "total_volume_kg": session.total_volume_kg,
        "duration_min": int((session.ended_at - session.started_at).total_seconds() / 60) if session.ended_at else None,
        "exercises_logged": len(session.exercises),
        "message": "Session completed!",
    }, None


def _log_exercise(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    sid = inp.get("session_id") or session_id
    if not sid:
        return {"error": "No active session. Call start_workout_session first."}, session_id

    exercise_name = inp.get("exercise_name", "")
    sets_raw = inp.get("sets", [])
    notes = inp.get("notes", "")

    sets_data = []
    for s in sets_raw:
        set_dict = {
            "set_number": s.get("set_number", 1),
            "reps": s.get("reps"),
            "weight_kg": s.get("weight_kg"),
            "duration_seconds": s.get("duration_seconds"),
            "rpe": s.get("rpe"),
            "is_warmup": s.get("is_warmup", False),
        }
        sets_data.append(set_dict)

    se = session_crud.log_exercise_to_session(db, sid, exercise_name, sets_data, notes)
    working_sets = [s for s in se.sets if not s.is_warmup]
    total_vol = sum((s.weight_kg or 0) * (s.reps or 0) for s in working_sets)

    return {
        "success": True,
        "exercise": se.exercise.name,
        "sets_logged": len(se.sets),
        "working_sets": len(working_sets),
        "total_volume_kg": round(total_vol, 1),
        "session_id": sid,
    }, sid


def _create_or_update_routine(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    routine_id = inp.get("routine_id")
    days_data = inp.get("days", [])

    # Normalize days to match schema
    normalized_days = []
    for d in days_data:
        exercises = []
        for ex in d.get("exercises", []):
            exercises.append({
                "exercise_name": ex.get("exercise_name", ""),
                "order_index": ex.get("order_index", 0),
                "target_sets": ex.get("target_sets", 3),
                "target_reps_min": ex.get("target_reps_min"),
                "target_reps_max": ex.get("target_reps_max"),
                "target_weight_kg": ex.get("target_weight_kg"),
                "target_rpe": ex.get("target_rpe"),
                "rest_seconds": ex.get("rest_seconds", 90),
                "notes": ex.get("notes"),
            })
        normalized_days.append({
            "day_number": d.get("day_number", 1),
            "name": d.get("name", f"Day {d.get('day_number', 1)}"),
            "day_of_week": d.get("day_of_week"),
            "exercises": exercises,
        })

    if routine_id:
        update_fields = {}
        for field in ("name", "description", "goal", "frequency_per_week"):
            if inp.get(field) is not None:
                update_fields[field] = inp[field]
        routine_crud.update_routine(db, routine_id, update_fields)
        routine = routine_crud.get_routine(db, routine_id)
    else:
        routine_data = {
            "name": inp.get("name", "New Routine"),
            "description": inp.get("description"),
            "goal": inp.get("goal", "general fitness"),
            "frequency_per_week": inp.get("frequency_per_week", len(normalized_days)),
            "source": "ai_generated",
            "days": normalized_days,
        }
        routine = routine_crud.create_routine(db, routine_data)

    if inp.get("activate") and routine:
        routine_crud.activate_routine(db, routine.id)

    return {
        "success": True,
        "routine_id": routine.id if routine else None,
        "name": routine.name if routine else None,
        "days": len(normalized_days),
        "activated": bool(inp.get("activate")),
    }, session_id


def _update_user_profile(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    updatable = (
        "name", "age", "weight_kg", "height_cm", "fitness_level",
        "primary_goal", "secondary_goals", "injuries_limitations",
        "preferred_workout_days", "session_duration_min", "equipment_available",
    )
    data = {}
    for field in updatable:
        val = inp.get(field)
        if val is not None:
            if field in ("secondary_goals", "equipment_available") and isinstance(val, list):
                data[field] = json.dumps(val)
            else:
                data[field] = val

    user_crud.update_user(db, data)
    return {"success": True, "updated_fields": list(data.keys())}, session_id


def _get_exercise_progress(db: Session, inp: dict, session_id: int | None) -> tuple[dict, int | None]:
    exercise_name = inp.get("exercise_name", "")
    days_back = inp.get("days_back", 90)

    exercise = find_or_create_exercise(db, exercise_name)
    progress = get_exercise_progress(db, exercise.id, days_back)

    # Return a compact summary for Claude
    history = progress.get("history", [])
    pb = progress.get("personal_best", {})
    trend = progress.get("trend", "insufficient_data")

    return {
        "exercise": exercise.name,
        "sessions_found": len(history),
        "personal_best": pb,
        "trend": trend,
        "recent": history[-3:] if history else [],
    }, session_id
