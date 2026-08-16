from __future__ import annotations

import json

from app.config import TIMEOUT_CLAUDE_COLLAB_S
from app.prompts import COLLAB_SYSTEM_PROMPT
from app.services.claude_client import create_structured_output
from app.utils.logger import get_logger
from app.validators.schemas import CollabChatMessage, CollabExtractOutput

log = get_logger(__name__)


async def extract_trip_from_chat(
    *,
    messages: list[CollabChatMessage],
    member_count: int,
) -> CollabExtractOutput:
    transcript = "\n".join(
        f"{item.display_name}: {item.body}" for item in messages if item.body.strip()
    )
    user = json.dumps(
        {
            "memberCount": member_count,
            "transcript": transcript,
            "instruction": "Extract one group trip. Fill missingFields only when a value cannot be inferred.",
        },
        indent=2,
    )
    result: CollabExtractOutput = await create_structured_output(
        system=COLLAB_SYSTEM_PROMPT,
        user=user,
        schema=CollabExtractOutput,
        tool_name="emit_group_trip",
        timeout_s=TIMEOUT_CLAUDE_COLLAB_S,
    )
    if result.travelers < member_count:
        result.travelers = member_count
    log.info(
        "collab extract",
        destination=result.destination,
        missing=result.missing_fields,
        travelers=result.travelers,
    )
    return result
