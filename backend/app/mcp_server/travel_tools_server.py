"""FastMCP travel-tools server. Logs go to stderr so stdio stays the protocol."""

from mcp.server.fastmcp import FastMCP

from app.mcp_server.tools.estimate_hotel_cost import estimate_hotel_cost
from app.mcp_server.tools.get_destination_facts import get_destination_facts
from app.mcp_server.tools.search_flights import search_flights
from app.validators.budget_normalizer import normalize_budget_value

mcp = FastMCP("travel-tools")


@mcp.tool()
async def search_flights_tool(origin: str, destination: str, start_date: str, end_date: str) -> dict:
    """Finds the cheapest real flight (including multi-airline combinations) for a
    route and date range via the Kiwi Tequila API. Always returns real, live-queried
    prices — never estimate a flight price yourself."""
    flights = await search_flights(origin, destination, start_date, end_date)
    return {"flights": [f.model_dump(by_alias=True) for f in flights]}


@mcp.tool()
async def get_destination_facts_tool(destination_slug: str) -> dict:
    """Returns curated real facts (attractions, neighborhoods, local tips, cost index)
    for a destination. Use this to ground itinerary content — do not invent attraction
    names or local details that aren't returned here."""
    facts = await get_destination_facts(destination_slug)
    return facts.model_dump(by_alias=True)


@mcp.tool()
async def estimate_hotel_cost_tool(destination_slug: str, tier: str) -> dict:
    """Returns a price-per-night estimate for a destination and star tier, derived
    from the destination's cost index. Use this instead of guessing a hotel price."""
    estimate = await estimate_hotel_cost(destination_slug, tier)  # type: ignore[arg-type]
    return estimate.model_dump(by_alias=True)


@mcp.tool()
def normalize_budget_tool(raw: str) -> dict:
    """Deterministically parses a budget string like '20k', '₹20,000', or '20000
    rupees' into a clean integer. Pure function, no reasoning required — call this
    rather than parsing budget text yourself."""
    return {"value": normalize_budget_value(raw)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
