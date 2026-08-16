from __future__ import annotations

from app.config import CACHE_TTL_FLIGHTS, CACHE_TTL_FLIGHTS_DURABLE, cache_key_flights
from app.db.repositories.flight_cache_repository import get_flight_cache, set_flight_cache
from app.services.cache_service import cache_get, cache_set
from app.services.kiwi_client import search_kiwi_flights
from app.utils.logger import get_logger
from app.validators.schemas import FlightOption

log = get_logger(__name__)


async def search_flights(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    travelers: int = 1,
) -> list[FlightOption]:
    key = cache_key_flights(origin, destination, start_date, end_date)
    hot = await cache_get(key)
    if isinstance(hot, list) and hot:
        log.info("flight cache hit (redis)", key=key)
        return [FlightOption.model_validate(item) for item in hot]

    durable = get_flight_cache(key)
    if durable:
        log.info("flight cache hit (postgres)", key=key)
        flights = [FlightOption.model_validate(item) for item in durable]
        await cache_set(key, [f.model_dump(by_alias=True) for f in flights], CACHE_TTL_FLIGHTS)
        return flights

    try:
        flights = await search_kiwi_flights(
            origin=origin,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            travelers=travelers,
        )
        if flights:
            await cache_set(key, [f.model_dump(by_alias=True) for f in flights], CACHE_TTL_FLIGHTS)
            set_flight_cache(key, flights, CACHE_TTL_FLIGHTS_DURABLE)
        return flights
    except Exception as exc:
        stale = get_flight_cache(key, allow_expired=True)
        if stale:
            log.warning("kiwi failed — serving stale durable flight cache", key=key, error=str(exc))
            return [FlightOption.model_validate(item) for item in stale]
        raise
