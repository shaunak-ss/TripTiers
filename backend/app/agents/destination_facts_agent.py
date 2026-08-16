from __future__ import annotations

import json

from app.config import TIMEOUT_CLAUDE_FACTS_S
from app.prompts import DESTINATION_FACTS_SYSTEM_PROMPT
from app.services.claude_client import create_structured_output
from app.utils.logger import get_logger
from app.validators.schemas import DestinationFactsAgentOutput

log = get_logger(__name__)


async def run_destination_facts_agent(query: str) -> DestinationFactsAgentOutput:
    user = json.dumps({"destinationQuery": query}, indent=2)
    result: DestinationFactsAgentOutput = await create_structured_output(
        system=DESTINATION_FACTS_SYSTEM_PROMPT,
        user=user,
        schema=DestinationFactsAgentOutput,
        tool_name="emit_destination_facts",
        timeout_s=TIMEOUT_CLAUDE_FACTS_S,
    )
    log.info("destination facts agent complete", city=result.city, country=result.country)
    return result
