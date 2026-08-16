from __future__ import annotations

import httpx

from app.config import CACHE_TTL_LOCATION, CITY_IATA, TIMEOUT_KIWI_S, cache_key_location, get_settings
from app.services.cache_service import cache_get, cache_set
from app.utils.dates import to_kiwi_date
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.utils.retry import default_retry
from app.validators.schemas import FlightLeg, FlightOption

log = get_logger(__name__)


@default_retry
async def _kiwi_get(path: str, params: dict[str, str]) -> dict:
    settings = get_settings()
    url = settings.kiwi_api_base.rstrip("/") + path
    async with httpx.AsyncClient(timeout=TIMEOUT_KIWI_S) as client:
        response = await client.get(
            url,
            params=params,
            headers={"apikey": settings.kiwi_api_key or "", "accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()


async def resolve_iata(query: str) -> str:
    trimmed = query.strip()
    if len(trimmed) == 3 and trimmed.isalpha():
        return trimmed.upper()
    alias = CITY_IATA.get(trimmed.lower())
    if alias:
        return alias

    key = cache_key_location(trimmed)
    cached = await cache_get(key)
    if isinstance(cached, str):
        return cached

    try:
        data = await _kiwi_get("/locations/query", {"term": query, "location_types": "city", "limit": "1"})
        code = (data.get("locations") or [{}])[0].get("code")
        if code:
            await cache_set(key, code, CACHE_TTL_LOCATION)
            return code
    except Exception as exc:  # noqa: BLE001
        log.warning("kiwi location lookup failed", query=query, error=str(exc))

    raise AppError(
        400,
        "origin_unresolved",
        f'Could not resolve "{query}" to an airport/city code. Try an IATA code (e.g. DEL) or a major city name.',
    )


def map_kiwi_flight(flight: dict) -> FlightOption:
    route = flight.get("route") or []
    legs = [
        FlightLeg(
            **{
                "from": leg.get("flyFrom") or leg.get("cityFrom"),
                "to": leg.get("flyTo") or leg.get("cityTo"),
                "carrier": leg.get("airline") or "Unknown",
            }
        )
        for leg in route
    ]
    airlines = flight.get("airlines") or []
    airline = airlines[0] if airlines else (legs[0].carrier if legs else "Unknown")
    duration = (flight.get("duration") or {}).get("total") or 0
    booking = flight.get("deep_link") or flight.get("deepLink") or "https://www.kiwi.com"
    if not legs:
        legs = [
            FlightLeg(
                **{
                    "from": flight.get("flyFrom", ""),
                    "to": flight.get("flyTo", ""),
                    "carrier": airline,
                }
            )
        ]
    return FlightOption(
        airline=airline,
        legs=legs,
        price=round(flight.get("price") or 0),
        duration_minutes=max(1, round(duration / 60)),
        booking_url=booking,
    )


def _mock_flights(origin: str, destination: str, travelers: int) -> list[FlightOption]:
    settings = get_settings()
    fly_from = CITY_IATA.get(origin.strip().lower(), origin[:3].upper())
    fly_to = CITY_IATA.get(destination.strip().lower(), "DPS")
    base = 28000 if settings.app_currency == "INR" else 340
    return [
        FlightOption(
            airline="Mock Air",
            legs=[
                FlightLeg(**{"from": fly_from, "to": fly_to, "carrier": "Mock Air"}),
                FlightLeg(**{"from": fly_to, "to": fly_from, "carrier": "Mock Air"}),
            ],
            price=base * max(1, travelers),
            duration_minutes=620,
            booking_url="https://www.kiwi.com",
        )
    ]


async def search_kiwi_flights(
    *,
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    travelers: int,
) -> list[FlightOption]:
    settings = get_settings()
    if settings.use_kiwi_mock:
        log.warning("KIWI_MOCK — returning a deterministic mock flight, not live Tequila data")
        return _mock_flights(origin, destination, travelers)

    fly_from = await resolve_iata(origin)
    fly_to = await resolve_iata(destination)
    log.info("kiwi search", fly_from=fly_from, fly_to=fly_to, start=start_date, end=end_date)

    try:
        data = await _kiwi_get(
            "/v2/search",
            {
                "fly_from": fly_from,
                "fly_to": fly_to,
                "date_from": to_kiwi_date(start_date),
                "date_to": to_kiwi_date(start_date),
                "return_from": to_kiwi_date(end_date),
                "return_to": to_kiwi_date(end_date),
                "curr": settings.app_currency,
                "adults": str(max(1, travelers)),
                "limit": "20",
                "sort": "price",
                "max_stopovers": "3",
            },
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in {401, 403} and settings.environment != "production":
            log.warning("kiwi unauthorized — falling back to mock flights")
            return _mock_flights(origin, destination, travelers)
        raise
    flights = [map_kiwi_flight(item) for item in data.get("data") or []]
    flights.sort(key=lambda f: (f.price, f.duration_minutes))
    return flights
