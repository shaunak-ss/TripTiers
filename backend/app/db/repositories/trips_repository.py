from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.services.supabase_client import get_supabase
from app.utils.logger import get_logger
from app.validators.schemas import FlightOption, ItineraryDay, Stay, TripResult, TripSearchInput, TripTier

log = get_logger(__name__)


def create_pending_trip(
    *,
    origin_city: str,
    destination_slug: str,
    start_date: str,
    end_date: str,
    budget_raw: str,
    budget_normalized: int,
    travelers: int,
    label: str | None = None,
) -> str:
    sb = get_supabase()
    result = sb.table("trips").insert(
        {
            "origin_city": origin_city,
            "destination_slug": destination_slug,
            "start_date": start_date,
            "end_date": end_date,
            "budget_input_raw": budget_raw,
            "budget_normalized": budget_normalized,
            "travelers": travelers,
            "status": "pending",
            "label": label,
        }
    ).execute()
    if not result.data:
        raise RuntimeError("Failed to create trip")
    return result.data[0]["id"]


def mark_trip_status(trip_id: str, status: str) -> None:
    get_supabase().table("trips").update({"status": status}).eq("id", trip_id).execute()


def persist_trip_result(result: TripResult) -> None:
    sb = get_supabase()
    for tier in result.tiers:
        tier_row = sb.table("trip_tiers").upsert(
            {
                "trip_id": result.trip_id,
                "tier": tier.tier,
                "total_price": tier.total_price,
                "flight": tier.flight.model_dump(by_alias=True),
                "stay": tier.stay.model_dump(by_alias=True),
                "highlights": tier.highlights,
            },
            on_conflict="trip_id,tier",
        ).execute()
        if not tier_row.data:
            raise RuntimeError("Failed to persist tier")
        tier_id = tier_row.data[0]["id"]
        sb.table("itinerary_days").delete().eq("trip_tier_id", tier_id).execute()
        if tier.itinerary:
            sb.table("itinerary_days").insert(
                [
                    {
                        "trip_tier_id": tier_id,
                        "day_number": day.day,
                        "title": day.title,
                        "morning": day.morning,
                        "afternoon": day.afternoon,
                        "evening": day.evening,
                    }
                    for day in tier.itinerary
                ]
            ).execute()
    sb.table("trips").update(
        {
            "status": "ready",
            "currency": result.currency,
            "group_preferences_summary": result.group_preferences_summary,
        }
    ).eq("id", result.trip_id).execute()


def get_trip_result(trip_id: str) -> dict | None:
    try:
        UUID(trip_id)
    except ValueError:
        return None
    sb = get_supabase()
    trip_res = sb.table("trips").select("*").eq("id", trip_id).limit(1).execute()
    if not trip_res.data:
        return None
    trip = trip_res.data[0]
    if trip["status"] == "pending":
        return {"status": "pending"}
    if trip["status"] == "failed":
        return {"status": "failed"}

    dest_res = (
        sb.table("destinations")
        .select("city, country")
        .eq("slug", trip["destination_slug"])
        .limit(1)
        .execute()
    )
    dest = dest_res.data[0] if dest_res.data else None
    destination_label = f"{dest['city']}, {dest['country']}" if dest else trip["destination_slug"]

    tiers_res = sb.table("trip_tiers").select("*").eq("trip_id", trip_id).execute()
    assembled: list[TripTier] = []
    for tier in tiers_res.data or []:
        days_res = (
            sb.table("itinerary_days")
            .select("*")
            .eq("trip_tier_id", tier["id"])
            .order("day_number")
            .execute()
        )
        assembled.append(
            TripTier(
                tier=tier["tier"],
                total_price=tier["total_price"],
                flight=FlightOption.model_validate(tier["flight"]),
                stay=Stay.model_validate(tier["stay"]),
                highlights=tier["highlights"] or [],
                itinerary=[
                    ItineraryDay(
                        day=d["day_number"],
                        title=d["title"],
                        morning=d["morning"],
                        afternoon=d["afternoon"],
                        evening=d["evening"],
                    )
                    for d in days_res.data or []
                ],
            )
        )

    order = ["backpacker", "comfort", "luxury"]
    assembled.sort(key=lambda t: order.index(t.tier) if t.tier in order else 99)
    result = TripResult(
        trip_id=trip_id,
        input=TripSearchInput(
            destination=destination_label,
            origin_city=trip["origin_city"],
            start_date=str(trip["start_date"]),
            end_date=str(trip["end_date"]),
            budget=trip["budget_normalized"],
            travelers=trip["travelers"],
        ),
        tiers=assembled,
        generated_at=str(trip.get("created_at") or datetime.now(timezone.utc).isoformat()),
        currency=trip.get("currency") or "USD",
        group_preferences_summary=trip.get("group_preferences_summary"),
        label=trip.get("label"),
    )
    return {"status": "ready", "result": result}


def save_trip(user_id: str, trip_id: str) -> None:
    sb = get_supabase()
    sb.table("saved_trips").upsert(
        {"user_id": user_id, "trip_id": trip_id, "saved_at": datetime.now(timezone.utc).isoformat()},
        on_conflict="user_id,trip_id",
    ).execute()


def list_saved_trips(user_id: str) -> list[dict]:
    sb = get_supabase()
    rows = (
        sb.table("saved_trips")
        .select("trip_id, saved_at")
        .eq("user_id", user_id)
        .order("saved_at", desc=True)
        .execute()
    )
    out: list[dict] = []
    for row in rows.data or []:
        found = get_trip_result(row["trip_id"])
        if not found or found.get("status") != "ready":
            continue
        result = found["result"]
        tier = next((item for item in result.tiers if item.tier == "comfort"), None)
        if tier is None and result.tiers:
            tier = result.tiers[0]
        if tier is None:
            continue
        out.append(
            {
                "tripId": result.trip_id,
                "tier": tier.tier,
                "destination": result.input.destination,
                "label": result.label,
                "startDate": result.input.start_date,
                "endDate": result.input.end_date,
                "savedAt": row.get("saved_at"),
            }
        )
    return out
