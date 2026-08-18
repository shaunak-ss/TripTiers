from __future__ import annotations

from datetime import datetime, timezone

from app.agents.destination_facts_agent import run_destination_facts_agent
from app.services.supabase_client import get_supabase
from app.utils.logger import get_logger
from app.utils.slug import parse_destination_name, slugify_destination
from app.validators.schemas import CuratedFacts, DestinationFacts, DestinationFactsAgentOutput

log = get_logger(__name__)


def _row_to_facts(row: dict) -> DestinationFacts:
    return DestinationFacts(
        slug=row["slug"],
        city=row["city"],
        country=row["country"],
        cost_index=float(row["cost_index"]),
        currency_code=row.get("currency_code") or "USD",
        curated_facts=CuratedFacts.model_validate(row.get("curated_facts") or {}),
        source=row.get("source") or "manual",
    )


def find_destination(query: str) -> DestinationFacts | None:
    sb = get_supabase()
    slug = slugify_destination(query)
    by_slug = sb.table("destinations").select("*").eq("slug", slug).limit(1).execute()
    if by_slug.data:
        return _row_to_facts(by_slug.data[0])

    all_rows = sb.table("destinations").select("*").execute()
    needle = query.strip().lower()
    for row in all_rows.data or []:
        city = str(row["city"]).lower()
        country = str(row["country"]).lower()
        full = f"{city}, {country}"
        city_part = needle.split(",")[0].strip()
        if city == needle or full == needle or city_part in city or city in needle:
            return _row_to_facts(row)
    return None


def _generic_fallback_facts(city: str) -> CuratedFacts:
    return CuratedFacts.model_validate(
        {
            "attractions": [
                {"name": f"{city} historic center", "note": "Walk the core and get oriented on day one."},
                {"name": f"{city} local market", "note": "Best place for food and people-watching."},
                {"name": f"A scenic viewpoint near {city}", "note": "Go near sunset if the weather is clear."},
            ],
            "neighborhoods": [
                {"name": "Old Town", "vibe": "Walkable, historic, good for first nights."},
                {"name": "City Center", "vibe": "Transit hub, mix of hotels and restaurants."},
                {"name": "Waterfront / park district", "vibe": "Slower pace, evening strolls."},
            ],
            "localTips": [
                f"Use local transit rather than assuming you need a taxi everywhere in {city}.",
                "Carry a bit of cash for small vendors.",
                "Check seasonal weather and any public holidays before locking outdoor days.",
            ],
            "stayIdeas": {
                "backpacker": [f"A well-reviewed hostel in {city} Old Town"],
                "comfort": [f"A 3–4 star hotel near {city} center"],
                "luxury": [f"A 5 star hotel in {city}"],
            },
        }
    )


async def bootstrap_destination(query: str) -> DestinationFacts:
    fallback_city, fallback_country, slug = parse_destination_name(query)
    cost_index = 1.0
    currency_code = "USD"
    source = "manual"

    try:
        agent_out: DestinationFactsAgentOutput = await run_destination_facts_agent(query)
        city, country = agent_out.city, agent_out.country
        cost_index = agent_out.cost_index
        currency_code = agent_out.currency_code
        facts = CuratedFacts.model_validate(
            {
                "attractions": [a.model_dump(by_alias=True) for a in agent_out.attractions],
                "neighborhoods": [n.model_dump(by_alias=True) for n in agent_out.neighborhoods],
                "localTips": agent_out.local_tips,
                "stayIdeas": agent_out.stay_ideas.model_dump(by_alias=True),
            }
        )
        source = "gemini"
    except Exception as exc:  # noqa: BLE001
        log.error("destination facts agent failed — using generic template", query=query, error=str(exc))
        city, country = fallback_city.title(), fallback_country.title()
        facts = _generic_fallback_facts(city)

    payload = {
        "slug": slug,
        "city": city,
        "country": country,
        "cost_index": cost_index,
        "currency_code": currency_code,
        "curated_facts": facts.model_dump(by_alias=True),
        "source": source,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    sb = get_supabase()
    result = sb.table("destinations").upsert(payload, on_conflict="slug").execute()
    if not result.data:
        raise RuntimeError("Failed to bootstrap destination")
    log.info("bootstrapped destination facts", slug=slug, source=source)
    return _row_to_facts(result.data[0])
