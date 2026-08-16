from fastapi import APIRouter

from app.agents.collab_agent import extract_trip_from_chat
from app.auth.deps import CurrentUserDep
from app.db.repositories import collab_repository as collab_repo
from app.orchestrator.trip_pipeline import run_trip_pipeline
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
        return collab_repo.add_message(
            code=code,
            user_id=user.id,
            display_name=user.name,
            body=text,
        )
    except KeyError as exc:
        raise AppError(404, "room_not_found", "That invite code does not match a room.") from exc
    except PermissionError as exc:
        raise AppError(403, "not_a_member", "Join this room before chatting.") from exc
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise _unavailable(exc) from exc


@router.post("/generate")
async def generate_from_chat(body: CollabGenerateBody, user: CurrentUserDep):
    if body.room_code:
        _member_room(body.room_code, user.id)
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
    log.info("collab generate pipeline", room=body.room_code, user=user.id, destination=payload.destination)
    trip = await run_trip_pipeline(payload, str(budget))
    if body.room_code:
        try:
            collab_repo.set_generated_trip(body.room_code, trip.trip_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not persist generated trip on room", error=str(exc))
    return {
        "trip": trip.model_dump(by_alias=True, mode="json"),
        "notes": extract.notes,
        "missingFields": [],
    }
