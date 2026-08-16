from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.itinerary_agent import fallback_itinerary
from app.utils.dates import to_kiwi_date, trip_length_days, trip_length_nights
from app.utils.slug import parse_destination_name, slugify_destination
from app.validators.schemas import CuratedFacts, DestinationFacts, TripSearchInput


def test_slugify():
    assert slugify_destination("Bali, Indonesia") == "bali-indonesia"
    assert slugify_destination("New York, USA") == "new-york-usa"


def test_parse_destination():
    city, country, slug = parse_destination_name("Tokyo, Japan")
    assert city == "Tokyo"
    assert country == "Japan"
    assert slug == "tokyo-japan"


def test_trip_length():
    assert trip_length_days("2026-09-01", "2026-09-05") == 5
    assert trip_length_nights("2026-09-01", "2026-09-05") == 4
    assert to_kiwi_date("2026-09-01") == "01/09/2026"


@pytest.mark.asyncio
async def test_pipeline_no_flights_raises():
    from app.orchestrator.trip_pipeline import run_trip_pipeline
    from app.utils.errors import AppError

    start = (date.today() + timedelta(days=30)).isoformat()
    end = (date.today() + timedelta(days=35)).isoformat()
    payload = TripSearchInput(
        destination="Bali, Indonesia",
        origin_city="Delhi",
        start_date=start,
        end_date=end,
        budget=1500,
        travelers=2,
    )

    dest = DestinationFacts(
        slug="bali-indonesia",
        city="Bali",
        country="Indonesia",
        cost_index=0.85,
        curated_facts=CuratedFacts.model_validate({"attractions": [{"name": "Ubud Monkey Forest"}]}),
    )

    with (
        patch("app.orchestrator.trip_pipeline.get_destination_facts", AsyncMock(return_value=dest)),
        patch("app.orchestrator.trip_pipeline.create_pending_trip", return_value="trip-1"),
        patch("app.orchestrator.trip_pipeline.mark_trip_status"),
        patch(
            "app.orchestrator.trip_pipeline.run_flight_search_agent",
            AsyncMock(side_effect=AppError(422, "no_flights_found", "none")),
        ),
    ):
        with pytest.raises(AppError) as exc:
            await run_trip_pipeline(payload, "1500")
        assert exc.value.code == "no_flights_found"


def test_fallback_itinerary_day_count():
    dest = DestinationFacts(
        slug="bali-indonesia",
        city="Bali",
        country="Indonesia",
        cost_index=0.85,
        curated_facts=CuratedFacts.model_validate(
            {
                "attractions": [{"name": "Ubud Monkey Forest"}],
                "neighborhoods": [{"name": "Ubud"}],
                "localTips": ["Bring a sarong."],
            }
        ),
    )
    days = fallback_itinerary(dest, 5, "comfort")
    assert len(days) == 5
    assert all(d.morning and d.afternoon and d.evening for d in days)
