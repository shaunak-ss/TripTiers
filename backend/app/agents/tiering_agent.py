import json

from app.config import TIMEOUT_CLAUDE_TIERING_S
from app.prompts import TIERING_SYSTEM_PROMPT
from app.services.claude_client import create_structured_output
from app.utils.logger import get_logger
from app.validators.schemas import DestinationFacts, FlightOption, HotelCostEstimate, TierId, TieringAgentOutput

log = get_logger(__name__)


async def run_tiering_agent(
    *,
    destination: DestinationFacts,
    flight: FlightOption,
    stays: dict[TierId, HotelCostEstimate],
    days: int,
    nights: int,
    budget: int,
    currency: str,
    travelers: int,
    origin_city: str,
) -> TieringAgentOutput:
    user = json.dumps(
        {
            "originCity": origin_city,
            "destination": f"{destination.city}, {destination.country}",
            "tripLengthDays": days,
            "nights": nights,
            "travelers": travelers,
            "userBudget": budget,
            "currency": currency,
            "cheapestFlight": flight.model_dump(by_alias=True),
            "stayEstimates": {k: v.model_dump() for k, v in stays.items()},
            "instruction": "Do not invent prices. Use stayIdeas for stayName. If userBudget < cheapestFlight.price, set budgetWarning.",
        },
        indent=2,
    )
    facts_block = {
        "type": "text",
        "text": "DESTINATION FACTS (grounding — stay names and highlights must come from here):\n"
        + json.dumps(destination.curated_facts.model_dump(by_alias=True), indent=2),
        "cache_control": {"type": "ephemeral"},
    }
    result = await create_structured_output(
        system=TIERING_SYSTEM_PROMPT,
        user=user,
        schema=TieringAgentOutput,
        tool_name="emit_tiers",
        timeout_s=TIMEOUT_CLAUDE_TIERING_S,
        extra_cached_blocks=[facts_block],
    )
    log.info("tiering agent complete", budget_warning=result.budget_warning)
    return result
