from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.agents.flight_search_agent import run_flight_search_agent
from app.agents.itinerary_agent import run_itinerary_agent
from app.agents.tiering_agent import run_tiering_agent
from app.config import DAILY_SPEND_BASE, STAY_TYPE, TIER_ORDER, get_settings
from app.db.repositories.trips_repository import create_pending_trip, mark_trip_status, persist_trip_result
from app.mcp_server.tools.estimate_hotel_cost import estimate_hotel_cost
from app.mcp_server.tools.get_destination_facts import get_destination_facts
from app.services.fx_client import get_fx_rate
from app.utils.dates import trip_length_days, trip_length_nights
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import FlightOption, HotelCostEstimate, Stay, TierId, TripResult, TripSearchInput, TripTier
from app.validators.trip_validator import validate_trip_result

log = get_logger(__name__)


def _total_price(
    flight: FlightOption,
    stay_per_night: int,
    nights: int,
    daily_spend: int,
    days: int,
    travelers: int,
) -> int:
    return round(flight.price + stay_per_night * nights + daily_spend * days * travelers)


async def run_trip_pipeline(input_data: TripSearchInput, budget_raw: str) -> TripResult:
    started = datetime.now(timezone.utc)
    days = trip_length_days(input_data.start_date, input_data.end_date)
    nights = trip_length_nights(input_data.start_date, input_data.end_date)
    settings = get_settings()

    destination = await get_destination_facts(input_data.destination)
    trip_id = create_pending_trip(
        origin_city=input_data.origin_city,
        destination_slug=destination.slug,
        start_date=input_data.start_date,
        end_date=input_data.end_date,
        budget_raw=budget_raw,
        budget_normalized=input_data.budget,
        travelers=input_data.travelers,
    )

    try:
        flight = await run_flight_search_agent(
            origin_city=input_data.origin_city,
            destination_city=destination.city,
            start_date=input_data.start_date,
            end_date=input_data.end_date,
            travelers=input_data.travelers,
        )

        stay_list = await asyncio.gather(
            *[
                estimate_hotel_cost(
                    destination.slug,
                    tier,
                    start_date=input_data.start_date,
                    end_date=input_data.end_date,
                    travelers=input_data.travelers,
                )
                for tier in TIER_ORDER
            ]
        )
        stays: dict[TierId, HotelCostEstimate] = {tier: est for tier, est in zip(TIER_ORDER, stay_list, strict=True)}
        daily_spend = {
            tier: round(DAILY_SPEND_BASE[settings.app_currency][tier] * destination.cost_index) for tier in TIER_ORDER
        }

        trip_currency = destination.currency_code
        fx_rate = 1.0
        if trip_currency != settings.app_currency:
            resolved_rate = await get_fx_rate(settings.app_currency, trip_currency)
            if resolved_rate is None:
                log.warning(
                    "fx rate unavailable — showing prices in app currency instead",
                    target=trip_currency,
                    app_currency=settings.app_currency,
                )
                trip_currency = settings.app_currency
            else:
                fx_rate = resolved_rate

        if fx_rate != 1.0:
            flight = flight.model_copy(update={"price": round(flight.price * fx_rate)})
            stays = {
                tier: est.model_copy(update={"price_per_night": round(est.price_per_night * fx_rate), "currency": trip_currency})
                for tier, est in stays.items()
            }
            daily_spend = {tier: round(v * fx_rate) for tier, v in daily_spend.items()}
        budget_in_trip_currency = round(input_data.budget * fx_rate)

        tiering = await run_tiering_agent(
            destination=destination,
            flight=flight,
            stays=stays,
            days=days,
            nights=nights,
            budget=budget_in_trip_currency,
            currency=trip_currency,
            travelers=input_data.travelers,
            origin_city=input_data.origin_city,
        )

        itinerary_results = await asyncio.gather(
            *[run_itinerary_agent(destination=destination, tier=tier, days=days) for tier in TIER_ORDER],
            return_exceptions=True,
        )

        tiers: list[TripTier] = []
        for tier, itinerary_result in zip(TIER_ORDER, itinerary_results, strict=True):
            stay = stays[tier]
            draft = next((t for t in tiering.tiers if t.tier == tier), None)
            if isinstance(itinerary_result, Exception):
                log.error("itinerary stage rejected", tier=tier, error=str(itinerary_result))
                days_out = []
            else:
                days_out = itinerary_result[0]

            highlights = list(draft.highlights if draft else [stay.type, "Cheapest real flight we found"])
            if tiering.budget_warning and tier == "backpacker":
                highlights = [tiering.budget_warning, *highlights]
            stay_name = draft.stay_name if draft else (stay.suggested_names[0] if stay.suggested_names else f"A {stay.type.lower()} in {destination.city}")
            stay_type = draft.stay_type if draft else STAY_TYPE[tier]

            tiers.append(
                TripTier(
                    tier=tier,
                    total_price=_total_price(flight, stay.price_per_night, nights, daily_spend[tier], days, input_data.travelers),
                    flight=flight,
                    stay=Stay(
                        name=stay_name,
                        type=stay_type,
                        price_per_night=stay.price_per_night,
                        booking_url=stay.booking_url,
                    ),
                    highlights=highlights[:4],
                    itinerary=days_out,
                )
            )

        needs_retry = [t for t in tiers if len(t.itinerary) != days]
        if needs_retry:
            log.warning("retrying failed itinerary stages once", tiers=[t.tier for t in needs_retry])
            retries = await asyncio.gather(
                *[run_itinerary_agent(destination=destination, tier=t.tier, days=days) for t in needs_retry]
            )
            for tier_model, retry in zip(needs_retry, retries, strict=True):
                if not isinstance(retry, Exception):
                    tier_model.itinerary = retry[0]

        result = TripResult(
            trip_id=trip_id,
            input=TripSearchInput(
                destination=f"{destination.city}, {destination.country}",
                origin_city=input_data.origin_city,
                start_date=input_data.start_date,
                end_date=input_data.end_date,
                budget=input_data.budget,
                travelers=input_data.travelers,
            ),
            tiers=tiers,
            generated_at=datetime.now(timezone.utc).isoformat(),
            currency=trip_currency,
        )

        issues = validate_trip_result(result, days, nights, fx_rate)
        blocking = [
            i
            for i in issues
            if "Itinerary" in i.message or "empty" in i.message or "Missing tiers" in i.message or "below flight" in i.message
        ]
        if blocking:
            log.error("trip failed deterministic validation", issues=[i.message for i in blocking])
            raise AppError(502, "validation_failed", "Generated trip failed quality checks. Please retry.", [i.message for i in blocking])

        persist_trip_result(result)
        elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        log.info("pipeline complete", trip_id=trip_id, ms=elapsed_ms)
        return result
    except Exception:
        mark_trip_status(trip_id, "failed")
        raise
