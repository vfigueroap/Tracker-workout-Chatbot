"""Builds the system prompt for Claude with prompt caching on static sections."""
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.crud.user import get_user
from backend.crud.routine import get_active_routine
from backend.crud.session import get_recent_sessions, get_active_session
from backend.services.progress_service import get_top_exercises_with_prs


STATIC_INSTRUCTIONS = """You are Flex, an expert personal trainer and workout optimization AI assistant.
You help users log workouts, track progress, and continuously optimize their training program.

## Your Capabilities
You can use tools to:
- Log exercises, sets, reps, and weight to the current session
- Start and end workout sessions
- Create and update workout routines
- Update the user's profile and goals
- Query historical performance data for specific exercises

## Tool Usage Rules
- If the user mentions completing exercise sets and no session is active, call start_workout_session FIRST, then log_exercise
- Call log_exercise IMMEDIATELY when the user reports completing sets — don't wait for confirmation
- After logging, give a brief, encouraging confirmation with key stats
- Call end_workout_session when the user signals they are done (e.g. "that's it", "finished", "done for today")
- When creating routines, ask: days/week, goals, equipment, time per session — then call create_or_update_routine
- Use get_exercise_progress when the user asks about their performance or you need data to suggest progressions

## Interaction Style
- Be concise during active workouts — a sentence or two is enough after logging
- Be more detailed during planning or analysis conversations
- Reference the user's actual history and patterns when giving advice
- All weights are in kg internally; display in kg unless user specifies otherwise
- Be encouraging but honest — point out plateaus and suggest fixes
- If the user says something ambiguous (e.g. "did squats"), ask for reps/weight before logging"""


def build_system_prompt(db: Session) -> list[dict]:
    """Returns a list of Anthropic content blocks with cache_control markers."""
    user = get_user(db)
    routine = get_active_routine(db)
    recent_sessions = get_recent_sessions(db, limit=4)
    top_exercises = get_top_exercises_with_prs(db, limit=10)
    active_session = get_active_session(db)

    # Section 2: user context (semi-static)
    user_context = _build_user_context(user, routine, recent_sessions, top_exercises)

    # Section 3: current session state (dynamic, no cache)
    session_context = _build_session_context(active_session)

    return [
        {
            "type": "text",
            "text": STATIC_INSTRUCTIONS,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": user_context,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": session_context,
        },
    ]


def _build_user_context(user, routine, recent_sessions, top_exercises) -> str:
    lines = ["\n## User Profile"]
    if user:
        lines.append(f"Name: {user.name}")
        if user.age:
            lines.append(f"Age: {user.age}")
        if user.weight_kg:
            lines.append(f"Weight: {user.weight_kg}kg")
        if user.height_cm:
            lines.append(f"Height: {user.height_cm}cm")
        lines.append(f"Fitness Level: {user.fitness_level}")
        lines.append(f"Primary Goal: {user.primary_goal}")
        try:
            secondary = json.loads(user.secondary_goals or "[]")
            if secondary:
                lines.append(f"Secondary Goals: {', '.join(secondary)}")
        except Exception:
            pass
        if user.injuries_limitations:
            lines.append(f"Injuries/Limitations: {user.injuries_limitations}")
        if user.preferred_workout_days:
            lines.append(f"Preferred Days: {user.preferred_workout_days}")
        lines.append(f"Session Duration Target: {user.session_duration_min} min")
        try:
            equipment = json.loads(user.equipment_available or "[]")
            if equipment:
                lines.append(f"Equipment: {', '.join(equipment)}")
        except Exception:
            pass
    else:
        lines.append("No profile set up yet. Ask the user for their goals and preferences.")

    lines.append("\n## Active Routine")
    if routine:
        lines.append(f'"{routine.name}" — {routine.frequency_per_week}x/week — Goal: {routine.goal}')
        for day in sorted(routine.days, key=lambda d: d.day_number):
            lines.append(f"\n  Day {day.day_number} — {day.name}:")
            for re in sorted(day.exercises, key=lambda e: e.order_index):
                reps_str = f"{re.target_reps_min}-{re.target_reps_max}" if re.target_reps_min else "?"
                weight_str = f" @ {re.target_weight_kg}kg" if re.target_weight_kg else ""
                lines.append(f"    - {re.exercise.name}: {re.target_sets}x{reps_str}{weight_str} (rest {re.rest_seconds}s)")
    else:
        lines.append("No active routine. Help the user create or choose one.")

    lines.append("\n## Recent Sessions (last 4)")
    if recent_sessions:
        for s in recent_sessions:
            duration = None
            if s.ended_at:
                duration = int((s.ended_at - s.started_at).total_seconds() / 60)
            day_name = s.routine_day.name if s.routine_day else "Free Workout"
            date_str = s.started_at.strftime("%Y-%m-%d")
            dur_str = f"{duration}min" if duration else "?"
            feeling_str = f" — Feeling: {s.overall_feeling}/5" if s.overall_feeling else ""
            lines.append(f"  {date_str} | {day_name} | {dur_str} | Vol: {s.total_volume_kg:.0f}kg{feeling_str}")
            for se in s.exercises[:5]:
                working = [st for st in se.sets if not st.is_warmup]
                if working:
                    max_w = max((st.weight_kg or 0) for st in working)
                    lines.append(f"    - {se.exercise.name}: {len(working)} sets, top {max_w}kg")
    else:
        lines.append("  No completed sessions yet.")

    lines.append("\n## Personal Records (top exercises)")
    if top_exercises:
        for ex in top_exercises:
            if ex["pr_weight_kg"]:
                lines.append(f"  - {ex['name']}: {ex['pr_weight_kg']}kg × {ex['pr_reps']} reps")
    else:
        lines.append("  No records yet.")

    return "\n".join(lines)


def _build_session_context(active_session) -> str:
    now = datetime.utcnow()
    lines = [f"\n## Current Context\nToday: {now.strftime('%Y-%m-%d %H:%M UTC')}"]

    if active_session:
        elapsed = int((now - active_session.started_at).total_seconds() / 60)
        day_name = active_session.routine_day.name if active_session.routine_day else "Free Workout"
        lines.append(f"\nActive Session (ID: {active_session.id}) — {day_name} — {elapsed} min elapsed")
        if active_session.exercises:
            lines.append("Exercises logged so far:")
            for se in active_session.exercises:
                working = [st for st in se.sets if not st.is_warmup]
                lines.append(f"  - {se.exercise.name}: {len(se.sets)} sets ({len(working)} working)")
        else:
            lines.append("No exercises logged yet in this session.")
    else:
        lines.append("\nNo active session. The user may be planning, asking questions, or about to start.")

    return "\n".join(lines)
