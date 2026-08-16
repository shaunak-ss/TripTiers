from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.agents.concierge_agent import BOT_DISPLAY_NAME, run_concierge_turn
from app.db.repositories import collab_repository as collab_repo
from app.services.trip_brief_fields import FIELD_LABELS, FIELD_OPTIONS, FIELD_ORDER, REQUIRED_FIELDS, normalize_field_value
from app.services.trip_generation import generate_trip_for_room
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import CollabChatMessage

log = get_logger(__name__)

_REPLY_DELAY_S = 6.0
# Per-process debounce state — one pending reply task per room. Multiple human messages
# (or a chip tap) in quick succession collapse into a single concierge turn once things
# pause. Not shared across worker processes; fine for a single-uvicorn-worker deployment.
_pending: dict[str, asyncio.Task] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def schedule_concierge_reply(room_code: str) -> None:
    code = room_code.upper()
    existing = _pending.get(code)
    if existing and not existing.done():
        existing.cancel()
    _pending[code] = asyncio.create_task(_run_after_delay(code))


async def _run_after_delay(room_code: str) -> None:
    try:
        await asyncio.sleep(_REPLY_DELAY_S)
    except asyncio.CancelledError:
        return
    try:
        await _run_concierge_turn(room_code)
    except Exception as exc:  # noqa: BLE001
        log.warning("concierge turn failed", room=room_code, error=str(exc))
    finally:
        _pending.pop(room_code, None)


def _last_human_sender(messages: list[dict]) -> tuple[str | None, str]:
    for message in reversed(messages):
        if not message.get("isBot"):
            return message.get("userId"), message.get("displayName") or "a member"
    return None, "a member"


def _last_bot_ask(messages: list[dict]) -> dict | None:
    for message in reversed(messages):
        if message.get("isBot") and message.get("kind") in ("choice", "text"):
            return message
    return None


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


async def _run_concierge_turn(room_code: str) -> None:
    room = collab_repo.get_room_by_code(room_code)
    if room is None:
        return

    messages = room.get("messages", [])
    if not any(not m.get("isBot") for m in messages):
        return

    brief: dict = dict(room.get("tripBrief") or {})

    # Skip only if we're still waiting on an answer to the last open question — a system
    # message (tap confirmation, correction, ready notice) or a fresh human message both
    # mean there's something new to process.
    last = messages[-1] if messages else None
    if last and last.get("isBot") and last.get("kind") in ("choice", "text"):
        open_field = (last.get("meta") or {}).get("field")
        if open_field and open_field not in brief:
            return

    last_ask = _last_bot_ask(messages)
    pending_generate_confirmation = bool(
        last_ask
        and last_ask.get("kind") == "choice"
        and (last_ask.get("meta") or {}).get("field") == "confirmGenerate"
        and not (last_ask.get("meta") or {}).get("resolved")
    )

    transcript = "\n".join(
        f"{BOT_DISPLAY_NAME if m.get('isBot') else m['displayName']}: {m['body']}"
        for m in messages
        if m.get("body", "").strip()
    )
    decision = await run_concierge_turn(
        transcript=transcript,
        member_count=len(room.get("members", [])),
        known_brief=brief,
        pending_generate_confirmation=pending_generate_confirmation,
    )
    set_by_user_id, set_by_name = _last_human_sender(messages)

    newly_resolved: list[tuple[str, str]] = []
    for answer in decision.resolved_fields:
        field = answer.field
        if field not in FIELD_ORDER or field in brief:
            continue
        normalized = normalize_field_value(field, answer.value)
        if normalized is None:
            continue
        value, option_label = normalized
        result = collab_repo.resolve_field(
            code=room_code,
            field=field,
            value=value,
            option_label=option_label,
            set_by_user_id=set_by_user_id,
            set_by_name=set_by_name,
            allow_overwrite=False,
        )
        if result is not None:
            brief[field] = result
            newly_resolved.append((field, result["optionLabel"]))

    if newly_resolved:
        if len(newly_resolved) == 1:
            field, label = newly_resolved[0]
            body = f"✅ {FIELD_LABELS.get(field, field)} set to {label}."
        else:
            body = "✅ " + " · ".join(f"{FIELD_LABELS.get(f, f)}: {label}" for f, label in newly_resolved)
        collab_repo.add_system_message(code=room_code, display_name=BOT_DISPLAY_NAME, body=body)

    if decision.changed_field and decision.changed_field in brief:
        field = decision.changed_field
        normalized = normalize_field_value(field, decision.changed_value)
        if normalized is not None:
            value, option_label = normalized
            result = collab_repo.resolve_field(
                code=room_code,
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
                    code=room_code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"🔄 {FIELD_LABELS.get(field, field)} updated to {result['optionLabel']}.",
                )

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
        await _trigger_generation(room_code, room)
    elif decision.generate_requested and not pending_generate_confirmation:
        existing_trip_id = room.get("generatedTripId")
        unchanged = bool(existing_trip_id) and brief == (room.get("generatedTripBrief") or {})
        if unchanged:
            collab_repo.add_system_message(
                code=room_code,
                display_name=BOT_DISPLAY_NAME,
                body="✅ Already generated with the current details — check Saved Trips or tap 'View itinerary' above.",
            )
        else:
            still_missing = [f for f in REQUIRED_FIELDS if f not in brief]
            if still_missing:
                labels = ", ".join(FIELD_LABELS.get(f, f) for f in still_missing)
                collab_repo.add_system_message(
                    code=room_code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"Almost there — I still need: {labels}.",
                )
            else:
                verb = "regenerate" if existing_trip_id else "generate"
                collab_repo.add_bot_message(
                    code=room_code,
                    display_name=BOT_DISPLAY_NAME,
                    body=f"Ready to {verb} the itinerary with what we've got so far?",
                    kind="choice",
                    meta={"field": "confirmGenerate", "options": ["Yes, generate it!", "Not yet"]},
                )

    if (
        decision.should_ask
        and decision.ask_field
        and decision.ask_field in FIELD_ORDER
        and decision.ask_field not in brief
    ):
        field = decision.ask_field
        options = FIELD_OPTIONS.get(field, [])
        kind = "choice" if options else "text"
        meta: dict = {"field": field}
        if options:
            meta["options"] = options
        body = decision.ask_message.strip() or f"What's the {FIELD_LABELS.get(field, field).lower()}?"
        collab_repo.add_bot_message(code=room_code, display_name=BOT_DISPLAY_NAME, body=body, kind=kind, meta=meta)

    if decision.ready_message.strip():
        collab_repo.add_system_message(
            code=room_code, display_name=BOT_DISPLAY_NAME, body="✅ " + decision.ready_message.strip()
        )

    log.info(
        "concierge turn applied",
        room=room_code,
        resolved=[f for f, _ in newly_resolved],
        changed=decision.changed_field or None,
        asked=decision.ask_field if decision.should_ask else None,
        generate_confirmed=decision.generate_confirmed,
        generate_requested=decision.generate_requested,
    )
