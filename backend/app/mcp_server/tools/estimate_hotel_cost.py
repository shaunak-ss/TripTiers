from urllib.parse import quote_plus

from app.config import HOTEL_BASE_NIGHTLY, STAY_TYPE, get_settings
from app.mcp_server.tools.get_destination_facts import get_destination_facts
from app.validators.schemas import HotelCostEstimate, TierId


async def estimate_hotel_cost(
    destination_slug: str,
    tier: TierId,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    travelers: int = 1,
) -> HotelCostEstimate:
    dest = await get_destination_facts(destination_slug)
    settings = get_settings()
    base = HOTEL_BASE_NIGHTLY[settings.app_currency][tier]
    price = max(1, round(base * dest.cost_index))
    ideas = []
    if dest.curated_facts.stay_ideas:
        ideas = getattr(dest.curated_facts.stay_ideas, tier) or []

    params = {"ss": f"{dest.city}, {dest.country}"}
    if start_date:
        params["checkin"] = start_date
    if end_date:
        params["checkout"] = end_date
    params["group_adults"] = str(max(1, travelers))
    params["no_rooms"] = "1"
    query = "&".join(f"{key}={quote_plus(value)}" for key, value in params.items())

    return HotelCostEstimate(
        destination_slug=dest.slug,
        tier=tier,
        price_per_night=price,
        currency=settings.app_currency,
        type=STAY_TYPE[tier],
        suggested_names=ideas,
        booking_url=f"https://www.booking.com/searchresults.html?{query}",
    )
