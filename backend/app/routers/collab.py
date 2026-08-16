from fastapi import APIRouter

from app.agents.collab_agent import extract_trip_from_chat
from app.agents.concierge_agent import BOT_DISPLAY_NAME
from app.auth.deps import CurrentUserDep
from app.db.repositories import collab_repository as collab_repo
from app.orchestrator.trip_pipeline import run_trip_pipeline
from app.services.concierge_debouncer import handle_generate_confirmation_select, schedule_concierge_reply
from app.services.trip_brief_fields import FIELD_LABELS, normalize_field_value
from app.services.trip_generation import build_group_preferences, generate_trip_for_room
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.budget_normalizer import normalize_budget_value
from app.validators.schemas import CamelModel, CollabGenerateBody, TripSearchInput

log = get_logger(__name__)
router = APIRouter(prefix="/api/collab", tags=["collab"])


class CollabRoomBody(CamelModel):
    name: str
    trip_id: str | None = None


class CollabJoinBody(CamelModel):
    code: str


class CollabMessageBody(CamelModel):
    body: str


class CollabSelectBody(CamelModel):
    value: str


def _unavailable(exc: Exception) -> AppError:
    log.warning("collab table missing or query failed", error=str(exc))
    return AppError(
        503,
        "collab_unavailable",
        "Collaboration tables are not set up yet. Run backend/app/db/collab_schema.sql in the Supabase SQL editor.",
    )


def _member_room(code: str, user_id: str) -> dict:
    room = collab_repo.get_room_by_code(code)
    if room is None:
        raise AppError(404, "room_not_found", "That invite code does not match a room.")
    try:
        collab_repo.assert_member(room, user_id)
    except PermissionError as exc:
        raise AppError(403, "not_a_member", "Join this room before chatting.") from exc
    return room


@router.post("/rooms")
async def create_room(body: CollabRoomBody, user: CurrentUserDep):
    try:
        return collab_repo.create_room(
            name=body.name.strip() or f"{user.name}'s trip room",
            host_user_id=user.id,
            display_name=user.name,
            email=user.email,
            trip_id=body.trip_id,
        )
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.post("/rooms/join")
async def join_room(body: CollabJoinBody, user: CurrentUserDep):
    try:
        return collab_repo.join_room(
            code=body.code,
            user_id=user.id,
            display_name=user.name,
            email=user.email,
        )
    except KeyError as exc:
        raise AppError(404, "room_not_found", "That invite code does not match a room.") from exc
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.get("/rooms/{code}")
async def get_room(code: str, user: CurrentUserDep):
    try:
        return _member_room(code, user.id)
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.post("/rooms/{code}/messages")
async def post_message(code: str, body: CollabMessageBody, user: CurrentUserDep):
    text = body.body.strip()
    if not text:
        raise AppError(400, "validation_error", "Write a message first.")
    try:
        message = collab_repo.add_message(
            code=code,
            user_id=user.id,
            display_name=user.name,
            body=text,
        )
        schedule_concierge_reply(code)
        return message
    except KeyError as exc:
        raise AppError(404, "room_not_found", "That invite code does not match a room.") from exc
    except PermissionError as exc:
        raise AppError(403, "not_a_member", "Join this room before chatting.") from exc
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.post("/rooms/{code}/messages/{message_id}/select")
async def select_option(code: str, message_id: str, body: CollabSelectBody, user: CurrentUserDep):
    try:
        room = _member_room(code, user.id)
        message = collab_repo.get_message(message_id)
        if message is None or message["roomId"] != room["id"] or message["kind"] != "choice":
            raise AppError(404, "message_not_found", "That question no longer exists.")

        field = (message.get("meta") or {}).get("field")
        if not field:
            raise AppError(400, "invalid_selection", "This message isn't a selectable question.")

        if field == "confirmGenerate":
            result = await handle_generate_confirmation_select(
                room=room, message=message, value=body.value, actor_user_id=user.id, actor_name=user.name
            )
            return result

        normalized = normalize_field_value(field, body.value)
        if normalized is None:
            raise AppError(400, "invalid_selection", "Could not understand that selection.")
        value, option_label = normalized

        already_resolved = bool(room["tripBrief"].get(field))
        result = collab_repo.resolve_field(
            code=code,
            field=field,
            value=value,
            option_label=option_label,
            set_by_user_id=user.id,
            set_by_name=user.name,
            allow_overwrite=False,
        )
        if result is None:
            raise AppError(404, "room_not_found", "That invite code does not match a room.")

        collab_repo.set_message_resolved_meta(message_id, result)
        if not already_resolved:
            collab_repo.add_system_message(
                code=code,
                display_name=BOT_DISPLAY_NAME,
                body=f"✅ {FIELD_LABELS.get(field, field)} set to {result['optionLabel']} — picked by {result['setByName']}.",
            )
            schedule_concierge_reply(code)

        meta = dict(message.get("meta") or {})
        meta["resolved"] = result
        return {**message, "meta": meta}
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.post("/generate")
async def generate_from_chat(body: CollabGenerateBody, user: CurrentUserDep):
    if body.room_code:
        room = _member_room(body.room_code, user.id)
        trip, notes = await generate_trip_for_room(
            room=room, messages=body.messages, member_count=body.member_count
        )
        return {
            "trip": trip.model_dump(by_alias=True, mode="json"),
            "notes": notes,
            "missingFields": [],
        }

    # No room context (legacy/generic path) — no brief, no dedup, no auto-save.
    extract = await extract_trip_from_chat(messages=body.messages, member_count=body.member_count)
    missing = list(extract.missing_fields)
    if not extract.destination.strip():
        missing.append("destination")
    if not extract.origin_city.strip():
        missing.append("originCity")
    if not extract.start_date.strip():
        missing.append("startDate")
    if not extract.end_date.strip():
        missing.append("endDate")
    budget = extract.budget
    if budget <= 0:
        parsed = normalize_budget_value(str(extract.budget)) if extract.budget else None
        if parsed:
            budget = parsed
        else:
            missing.append("budget")
    missing = list(dict.fromkeys(missing))
    if missing:
        raise AppError(
            422,
            "collab_incomplete",
            "The group chat does not have enough agreement to build a trip yet. Keep discussing, then generate again.",
            details=missing,
        )

    payload = TripSearchInput(
        destination=extract.destination.strip(),
        origin_city=extract.origin_city.strip(),
        start_date=extract.start_date,
        end_date=extract.end_date,
        budget=budget,
        travelers=max(body.member_count, extract.travelers, 1),
    )
    preferences_text, preferences_summary = build_group_preferences(extract, {})
    trip = await run_trip_pipeline(
        payload,
        str(budget),
        group_preferences=preferences_text,
        group_preferences_summary=preferences_summary,
    )
    return {
        "trip": trip.model_dump(by_alias=True, mode="json"),
        "notes": extract.notes,
        "missingFields": [],
    }
