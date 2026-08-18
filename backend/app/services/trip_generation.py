from __future__ import annotations

from app.agents.collab_agent import extract_trip_from_chat
from app.db.repositories import collab_repository as collab_repo
from app.db.repositories import trips_repository as trips_repo
from app.orchestrator.trip_pipeline import run_trip_pipeline
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.budget_normalizer import normalize_budget_value
from app.validators.schemas import CollabChatMessage, CollabExtractOutput, TripResult
from app.validators.schemas import TripSearchInput

log = get_logger(__name__)


def _brief_str(brief: dict, field: str) -> str | None:
    entry = brief.get(field)
    if not entry:
        return None
    value = str(entry.get("value") or "").strip()
    return value or None


def build_group_preferences(extract: CollabExtractOutput, brief: dict) -> tuple[str | None, str | None]:
    detail_parts = []
    tier_entry = brief.get("tier")
    if tier_entry and tier_entry.get("value"):
        detail_parts.append(f"Preferred trip style: {tier_entry['value']}")
    pace_entry = brief.get("pace")
    pace = pace_entry["value"] if pace_entry and pace_entry.get("value") else extract.pace
    if pace:
        detail_parts.append("Pace: " + pace)
    dietary_entry = brief.get("dietary")
    dietary = dietary_entry["value"] if dietary_entry and dietary_entry.get("value") else extract.dietary
    if dietary:
        detail_parts.append("Dietary: " + dietary)
    if extract.interests:
        detail_parts.append("Interests: " + ", ".join(extract.interests))
    if extract.must_sees:
        detail_parts.append("Must-see: " + ", ".join(extract.must_sees))
    if extract.notes:
        detail_parts.append("Notes: " + extract.notes)
    if not detail_parts:
        return None, None
    preferences_text = "\n".join(detail_parts)

    summary_bits = []
    if extract.interests:
        summary_bits.append(", ".join(extract.interests[:3]))
    if pace:
        summary_bits.append(f"{pace} pace")
    if dietary:
        summary_bits.append(dietary)
    summary = "Built around: " + " · ".join(summary_bits) if summary_bits else None
    return preferences_text, summary


async def generate_trip_for_room(
    *,
    room: dict,
    messages: list[CollabChatMessage],
    member_count: int,
) -> tuple[TripResult, str]:
    """(Re)generates the one trip a room owns, or hands back the existing one unchanged if
    nothing in tripBrief has moved since it was last generated. Never creates a second trip
    for the same room — a change reuses and overwrites the same trip_id. Saves the result to
    every current room member's Saved Trips, labeled with the room's name.

    Raises AppError(422, "collab_incomplete", ...) if required fields are still missing.
    """
    brief: dict = room.get("tripBrief") or {}
    code = room["code"]

    existing_trip_id = room.get("generatedTripId")
    if existing_trip_id and brief == (room.get("generatedTripBrief") or {}):
        existing = trips_repo.get_trip_result(existing_trip_id)
        if existing and existing.get("status") == "ready":
            log.info("collab generate — reusing unchanged trip", room=code, trip_id=existing_trip_id)
            return existing["result"], ""

    extract = await extract_trip_from_chat(messages=messages, member_count=member_count)

    destination = _brief_str(brief, "destination") or extract.destination.strip()
    origin_city = _brief_str(brief, "originCity") or extract.origin_city.strip()
    start_date = _brief_str(brief, "startDate") or extract.start_date
    end_date = _brief_str(brief, "endDate") or extract.end_date

    missing = list(extract.missing_fields)
    if not destination:
        missing.append("destination")
    if not origin_city:
        missing.append("originCity")
    if not start_date:
        missing.append("startDate")
    if not end_date:
        missing.append("endDate")

    budget = 0
    brief_budget = _brief_str(brief, "budget")
    if brief_budget and brief_budget.isdigit():
        budget = int(brief_budget)
    if budget <= 0:
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

    brief_travelers = _brief_str(brief, "travelers")
    travelers = int(brief_travelers) if brief_travelers and brief_travelers.isdigit() else extract.travelers

    payload = TripSearchInput(
        destination=destination,
        origin_city=origin_city,
        start_date=start_date,
        end_date=end_date,
        budget=budget,
        travelers=max(member_count, travelers, 1),
    )
    preferences_text, preferences_summary = build_group_preferences(extract, brief)
    log.info(
        "collab generate pipeline",
        room=code,
        destination=payload.destination,
        personalized=bool(preferences_text),
        reuse=bool(existing_trip_id),
    )
    trip = await run_trip_pipeline(
        payload,
        str(budget),
        group_preferences=preferences_text,
        group_preferences_summary=preferences_summary,
        reuse_trip_id=existing_trip_id,
        label=room.get("name"),
    )

    try:
        collab_repo.set_generated_trip(code, trip.trip_id, brief)
    except Exception as exc:  # noqa: BLE001
        log.warning("could not persist generated trip on room", room=code, error=str(exc))
    for member in room.get("members", []):
        try:
            trips_repo.save_trip(member["userId"], trip.trip_id)
        except Exception as exc:  # noqa: BLE001
            log.warning("could not save trip for member", member=member.get("userId"), error=str(exc))

    return trip, extract.notes
