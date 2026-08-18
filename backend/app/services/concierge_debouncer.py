from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from app.agents.concierge_agent import BOT_DISPLAY_NAME, run_concierge_turn
from app.db.repositories import collab_repository as collab_repo
from app.services.trip_brief_fields import (
    FIELD_LABELS,
    FIELD_OPTIONS,
    FIELD_ORDER,
    REQUIRED_FIELDS,
    normalize_field_value,
)
from app.services.trip_generation import generate_trip_for_room
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import CollabChatMessage

log = get_logger(__name__)

_welcome_locks: dict[str, asyncio.Lock] = {}

WELCOME_BODY = (
    "Hi! I'm TripTiers Assistant. I only change the trip when you ask me to — type `/assistant` followed by "
    "what you want, e.g. `/assistant 4 day trip to Thailand from Delhi, budget 2000`, and I'll update just "
    "that. Tap Generate above whenever the trip looks ready."
)

# Accepts "/assistant" and the common typo "/assitant", case-insensitive.
_COMMAND_PATTERN = re.compile(r"^/(assistant|assitant)\b\s*(.*)$", re.IGNORECASE | re.DOTALL)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def extract_assistant_command(text: str) -> str | None:
    """Returns the instruction text after '/assistant' (or the '/assitant' typo), or None
    if the message isn't a command at all."""
    match = _COMMAND_PATTERN.match(text.strip())
    if not match:
        return None
    return match.group(2).strip()


def _last_bot_ask(messages: list[dict]) -> dict | None:
    for message in reversed(messages):
        if message.get("isBot") and message.get("kind") in ("choice", "text"):
            return message
    return None


async def ensure_assistant_welcome(room: dict) -> dict:
    """Post the assistant's one-time intro so it's visible as soon as the room loads.

    This is informational only — it never asks a question. The assistant stays silent
    until someone sends an explicit /assistant command."""
    code = str(room.get("code") or "").upper()
    if not code:
        return room
    if any(message.get("isBot") for message in room.get("messages") or []):
        return room

    lock = _welcome_locks.setdefault(code, asyncio.Lock())
    async with lock:
        fresh = collab_repo.get_room_by_code(code) or room
        if any(message.get("isBot") for message in fresh.get("messages") or []):
            return fresh
        collab_repo.add_system_message(code=code, display_name=BOT_DISPLAY_NAME, body=WELCOME_BODY)
        log.info("concierge welcome posted", room=code)
        return collab_repo.get_room_by_code(code) or fresh


async def _trigger_generation(room_code: str, room: dict) -> None:
    messages_payload = [
        CollabChatMessage(displayName=m["displayName"], body=m["body"], createdAt=m["createdAt"])
        for m in room.get("messages", [])
        if m.get("body", "").strip()
    ]
    try:
        await generate_trip_for_room(
            room=room, messages=messages_payload, member_count=len(room.get("members", []))
        )
        collab_repo.add_system_message(
            code=room_code,
            display_name=BOT_DISPLAY_NAME,
            body="🎉 Itinerary is ready — saved to everyone's Saved Trips. Tap 'View itinerary' above to see it.",
        )
    except AppError as exc:
        collab_repo.add_system_message(
            code=room_code, display_name=BOT_DISPLAY_NAME, body=f"⚠️ Couldn't generate yet — {exc.message}"
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("chat-triggered generation failed", room=room_code, error=str(exc))
        collab_repo.add_system_message(
            code=room_code,
            display_name=BOT_DISPLAY_NAME,
            body="⚠️ Something went wrong generating the itinerary. Try the Generate button instead.",
        )


async def handle_generate_confirmation_select(
    *, room: dict, message: dict, value: str, actor_user_id: str, actor_name: str
) -> dict:
    is_yes = value.strip().lower().startswith("yes")
    resolved = {
        "value": "yes" if is_yes else "no",
        "optionLabel": value,
        "setByUserId": actor_user_id,
        "setByName": actor_name,
        "setAt": _now(),
    }
    collab_repo.set_message_resolved_meta(message["id"], resolved)
    if is_yes:
        await _trigger_generation(room["code"], room)
    meta = dict(message.get("meta") or {})
    meta["resolved"] = resolved
    return {**message, "meta": meta}


async def run_assistant_command(*, room_code: str, command_text: str, actor_user_id: str, actor_name: str) -> None:
    """Applies exactly what one /assistant command asks for — never asks a follow-up
    question or announces "ready" on its own. Only reacts to what's explicitly
    stated in `command_text`, including answering an explicit "what are my options
    for X" question with a tappable-chip message when the field has one."""
    code = room_code.upper()
    room = collab_repo.get_room_by_code(code)
    if room is None:
        return

    brief: dict = dict(room.get("tripBrief") or {})
    messages = room.get("messages", [])
    last_ask = _last_bot_ask(messages)
    pending_generate_confirmation = bool(
        last_ask
        and last_ask.get("kind") == "choice"
        and (last_ask.get("meta") or {}).get("field") == "confirmGenerate"
        and not (last_ask.get("meta") or {}).get("resolved")
    )

    transcript = f"{actor_name}: {command_text}"

    try:
        decision = await run_concierge_turn(
            transcript=transcript,
            member_count=len(room.get("members", [])),
            known_brief=brief,
            pending_generate_confirmation=pending_generate_confirmation,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("assistant command failed", room=code, error=str(exc))
        collab_repo.add_system_message(
            code=code,
            display_name=BOT_DISPLAY_NAME,
            body="⚠️ Couldn't process that just now — try rephrasing your /assistant command.",
        )
        return

    set_by_user_id, set_by_name = actor_user_id, actor_name

    # Any room member can set or later change any field — first-write-wins only
    # matters for concurrent picks landing in the same instant, not for who
    # "owns" a field afterwards, so this always overwrites.
    newly_set: list[tuple[str, str]] = []
    updated: list[tuple[str, str]] = []
    for answer in decision.resolved_fields:
        field = answer.field
        if field not in FIELD_ORDER:
            continue
        normalized = normalize_field_value(field, answer.value)
        if normalized is None:
            continue
        value, option_label = normalized
        was_resolved = field in brief
        result = collab_repo.resolve_field(
            code=code,
            field=field,
            value=value,
            option_label=option_label,
            set_by_user_id=set_by_user_id,
            set_by_name=set_by_name,
            allow_overwrite=True,
        )
        if result is not None:
            brief[field] = result
            (updated if was_resolved else newly_set).append((field, result["optionLabel"]))

    if newly_set:
        if len(newly_set) == 1:
            field, label = newly_set[0]
            body = f"✅ {FIELD_LABELS.get(field, field)} set to {label}."
        else:
            body = "✅ " + " · ".join(f"{FIELD_LABELS.get(f, f)}: {label}" for f, label in newly_set)
        collab_repo.add_system_message(code=code, display_name=BOT_DISPLAY_NAME, body=body)

    if updated:
        if len(updated) == 1:
            field, label = updated[0]
            body = f"🔄 {FIELD_LABELS.get(field, field)} updated to {label}."
        else:
            body = "🔄 " + " · ".join(f"{FIELD_LABELS.get(f, f)}: {label}" for f, label in updated)
        collab_repo.add_system_message(code=code, display_name=BOT_DISPLAY_NAME, body=body)

    newly_resolved = newly_set + updated

    if decision.changed_field and decision.changed_field in brief:
        field = decision.changed_field
        normalized = normalize_field_value(field, decision.changed_value)
        if normalized is not None:
            value, option_label = normalized
            result = collab_repo.resolve_field(
                code=code,
                field=field,
                value=value,
                option_label=option_label,
                set_by_user_id=set_by_user_id,
                set_by_name=set_by_name,
                allow_overwrite=True,
            )
            if result is not None:
                brief[field] = result
                collab_repo.add_system_message(
                    code=code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"🔄 {FIELD_LABELS.get(field, field)} updated to {result['optionLabel']}.",
                )

    if decision.should_ask and decision.ask_field:
        field = decision.ask_field
        options = decision.ask_options or FIELD_OPTIONS.get(field) or []
        body = decision.ask_message or f"Here are the options for {FIELD_LABELS.get(field, field)}:"
        if options:
            collab_repo.add_bot_message(
                code=code,
                display_name=BOT_DISPLAY_NAME,
                body=body,
                kind="choice",
                meta={"field": field, "options": options},
            )
        else:
            collab_repo.add_bot_message(code=code, display_name=BOT_DISPLAY_NAME, body=body, kind="text")

    if decision.generate_confirmed and pending_generate_confirmation and last_ask:
        resolved = {
            "value": "yes",
            "optionLabel": "Yes, generate it!",
            "setByUserId": set_by_user_id,
            "setByName": set_by_name,
            "setAt": _now(),
        }
        collab_repo.set_message_resolved_meta(last_ask["id"], resolved)
        room["tripBrief"] = brief
        await _trigger_generation(code, room)
    elif decision.generate_requested and not pending_generate_confirmation:
        existing_trip_id = room.get("generatedTripId")
        unchanged = bool(existing_trip_id) and brief == (room.get("generatedTripBrief") or {})
        if unchanged:
            collab_repo.add_system_message(
                code=code,
                display_name=BOT_DISPLAY_NAME,
                body="✅ Already generated with the current details — check Saved Trips or tap 'View itinerary' above.",
            )
        else:
            still_missing = [f for f in REQUIRED_FIELDS if f not in brief]
            if still_missing:
                labels = ", ".join(FIELD_LABELS.get(f, f) for f in still_missing)
                collab_repo.add_system_message(
                    code=code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"I can generate it, but I still need: {labels}. Send another /assistant command with those details first.",
                )
            else:
                verb = "regenerate" if existing_trip_id else "generate"
                collab_repo.add_bot_message(
                    code=code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"Ready to {verb} the itinerary with what we've got so far?",
                    kind="choice",
                    meta={"field": "confirmGenerate", "options": ["Yes, generate it!", "Not yet"]},
                )

    if (
        not newly_resolved
        and not decision.changed_field
        and not decision.generate_confirmed
        and not decision.generate_requested
        and not (decision.should_ask and decision.ask_field)
    ):
        collab_repo.add_system_message(
            code=code,
            display_name=BOT_DISPLAY_NAME,
            body="I didn't catch anything to change there — try `/assistant <what you want>`, e.g. "
            "`/assistant 4 day trip to Thailand, budget 2000`.",
        )

    log.info(
        "assistant command applied",
        room=code,
        resolved=[f for f, _ in newly_resolved],
        changed=decision.changed_field or None,
        answered_options_for=decision.ask_field if decision.should_ask else None,
        generate_confirmed=decision.generate_confirmed,
        generate_requested=decision.generate_requested,
    )
