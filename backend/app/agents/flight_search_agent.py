from app.mcp_server.tools.search_flights import search_flights
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import FlightOption

log = get_logger(__name__)


async def run_flight_search_agent(
    *,
    origin_city: str,
    destination_city: str,
    start_date: str,
    end_date: str,
    travelers: int,
) -> FlightOption:
    try:
        flights = await search_flights(origin_city, destination_city, start_date, end_date, travelers)
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        log.error("flight search agent failed", error=str(exc))
        raise AppError(
            503,
            "kiwi_unavailable",
            "We couldn't reach live flight data right now, and there's no recent cached price for this route. Try again in a few minutes.",
        ) from exc

    if not flights:
        raise AppError(
            422,
            "no_flights_found",
            f"No flights found from {origin_city} to {destination_city} for those dates. Try nearby dates or another origin city.",
        )

    cheapest = flights[0]
    log.info("cheapest flight selected", price=cheapest.price, airline=cheapest.airline)
    return cheapest
