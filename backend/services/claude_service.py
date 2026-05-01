"""Claude API integration with tool dispatch loop and prompt caching."""
import json
import anthropic
from sqlalchemy.orm import Session

from backend.config import settings
from backend.crud import conversation as conv_crud
from backend.crud.session import get_active_session
from backend.services.context_builder import build_system_prompt
from backend.services.tool_handlers import handle_tool

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "log_exercise",
        "description": (
            "Log a completed exercise with its sets to the current workout session. "
            "Call this immediately whenever the user reports finishing sets of any exercise. "
            "If no session is active, call start_workout_session first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "exercise_name": {
                    "type": "string",
                    "description": "Name of the exercise (e.g. 'Barbell Back Squat'). Will be fuzzy-matched or created.",
                },
                "session_id": {
                    "type": "integer",
                    "description": "The current workout session ID.",
                },
                "sets": {
                    "type": "array",
                    "description": "Array of sets performed.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "set_number": {"type": "integer"},
                            "reps": {"type": "integer"},
                            "weight_kg": {"type": "number"},
                            "duration_seconds": {"type": "integer"},
                            "rpe": {"type": "number"},
                            "is_warmup": {"type": "boolean"},
                        },
                        "required": ["set_number"],
                    },
                },
                "notes": {"type": "string"},
            },
            "required": ["exercise_name", "session_id", "sets"],
        },
    },
    {
        "name": "start_workout_session",
        "description": (
            "Start a new workout session. Call this when the user indicates they are beginning a workout. "
            "Returns the new session_id which must be passed to log_exercise calls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "routine_id": {"type": "integer", "description": "ID of the routine this session follows. Optional."},
                "routine_day_id": {"type": "integer", "description": "Specific day within the routine. Optional."},
                "notes": {"type": "string"},
            },
        },
    },
    {
        "name": "end_workout_session",
        "description": (
            "End and finalize the current workout session. "
            "Call when user says they are done (e.g. 'that's it', 'finished', 'done for today')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "integer"},
                "overall_feeling": {"type": "integer", "minimum": 1, "maximum": 5},
                "notes": {"type": "string"},
                "status": {"type": "string", "enum": ["completed", "abandoned"]},
            },
            "required": ["session_id"],
        },
    },
    {
        "name": "create_or_update_routine",
        "description": (
            "Create a new workout routine or update an existing one. "
            "Use when the user asks to build a program, modify their routine, or parse an uploaded routine."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "routine_id": {"type": "integer", "description": "If updating, provide its ID. Omit to create new."},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "goal": {"type": "string"},
                "frequency_per_week": {"type": "integer"},
                "activate": {"type": "boolean", "description": "Set as active routine after saving."},
                "days": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "day_number": {"type": "integer"},
                            "name": {"type": "string"},
                            "day_of_week": {"type": "string"},
                            "exercises": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "exercise_name": {"type": "string"},
                                        "order_index": {"type": "integer"},
                                        "target_sets": {"type": "integer"},
                                        "target_reps_min": {"type": "integer"},
                                        "target_reps_max": {"type": "integer"},
                                        "target_weight_kg": {"type": "number"},
                                        "target_rpe": {"type": "number"},
                                        "rest_seconds": {"type": "integer"},
                                        "notes": {"type": "string"},
                                    },
                                    "required": ["exercise_name", "target_sets"],
                                },
                            },
                        },
                        "required": ["day_number", "name", "exercises"],
                    },
                },
            },
            "required": ["name", "days"],
        },
    },
    {
        "name": "update_user_profile",
        "description": (
            "Update the user's profile: goals, body measurements, fitness level, preferences. "
            "Call when the user mentions a change in goals, situation, or provides physical stats."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "weight_kg": {"type": "number"},
                "height_cm": {"type": "number"},
                "fitness_level": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                "primary_goal": {"type": "string"},
                "secondary_goals": {"type": "array", "items": {"type": "string"}},
                "injuries_limitations": {"type": "string"},
                "preferred_workout_days": {"type": "string"},
                "session_duration_min": {"type": "integer"},
                "equipment_available": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
    {
        "name": "get_exercise_progress",
        "description": (
            "Retrieve historical performance data for a specific exercise. "
            "Use when the user asks about their progress, PRs, or when making progression recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "exercise_name": {"type": "string"},
                "days_back": {"type": "integer", "default": 90},
                "include_warmups": {"type": "boolean", "default": False},
            },
            "required": ["exercise_name"],
        },
    },
]


async def get_claude_response(
    db: Session, user_message: str, session_id: int | None = None
) -> tuple[str, list[str], int | None]:
    """
    Main entry point. Returns (reply_text, tools_used, active_session_id).
    Implements the tool dispatch loop: call Claude → handle tools → repeat until end_turn.
    """
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    # Determine active session_id from DB if not provided
    if session_id is None:
        active = get_active_session(db)
        if active:
            session_id = active.id

    # Persist user message
    conv_crud.add_message(db, role="user", content=user_message, session_id=session_id)

    # Build conversation history (last 30 messages)
    history = conv_crud.get_recent_messages(db, limit=30)

    # Convert stored messages to Anthropic format, excluding the message we just added
    # (we'll add it fresh below)
    messages: list[dict] = []
    for msg in history[:-1]:  # exclude last (just-added user msg)
        if msg.role in ("user", "assistant") and msg.message_type == "text":
            messages.append({"role": msg.role, "content": msg.content})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    # Build system prompt with cache_control on stable sections
    system_blocks = build_system_prompt(db)

    tools_used: list[str] = []
    final_reply = ""

    # Tool dispatch loop
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_blocks,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            # Extract text reply
            for block in response.content:
                if block.type == "text":
                    final_reply = block.text
                    break
            # Persist assistant reply
            if final_reply:
                conv_crud.add_message(db, role="assistant", content=final_reply, session_id=session_id)
            break

        if response.stop_reason == "tool_use":
            # Append assistant response (including tool_use blocks) to history
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                    if block.text:
                        final_reply = block.text  # capture any text before tool use
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            messages.append({"role": "assistant", "content": assistant_content})

            # Execute all tool calls and collect results
            tool_result_content = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                tools_used.append(block.name)

                # Log tool call to conversation
                conv_crud.add_message(
                    db,
                    role="assistant",
                    content=json.dumps({"name": block.name, "input": block.input}),
                    session_id=session_id,
                    message_type="tool_use",
                    tool_name=block.name,
                    tool_use_id=block.id,
                )

                # Execute the tool
                result, session_id = handle_tool(db, block.name, block.input, session_id)
                result_str = json.dumps(result)

                # Log tool result
                conv_crud.add_message(
                    db,
                    role="assistant",
                    content=result_str,
                    session_id=session_id,
                    message_type="tool_result",
                    tool_name=block.name,
                    tool_use_id=block.id,
                )

                tool_result_content.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_str,
                })

            # Append tool results as user message
            messages.append({"role": "user", "content": tool_result_content})
        else:
            # Unexpected stop reason — break out
            for block in response.content:
                if hasattr(block, "text"):
                    final_reply = block.text
            break

    if not final_reply:
        final_reply = "Listo."

    # Persist final assistant reply if not already done
    if final_reply and (not history or history[-1].content != final_reply):
        last = conv_crud.get_recent_messages(db, limit=1)
        if not last or last[-1].role != "assistant" or last[-1].content != final_reply:
            conv_crud.add_message(db, role="assistant", content=final_reply, session_id=session_id)

    return final_reply, tools_used, session_id
