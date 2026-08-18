from __future__ import annotations

import json

from app.config import TIMEOUT_CLAUDE_CONCIERGE_S
from app.prompts import CONCIERGE_SYSTEM_PROMPT
from app.services.gemini_client import create_structured_output
from app.services.trip_brief_fields import FIELD_LABELS, FIELD_OPTIONS, FIELD_ORDER
from app.utils.dates import today_iso_date
from app.utils.logger import get_logger
from app.validators.schemas import ConciergeTurnOutput

log = get_logger(__name__)

BOT_DISPLAY_NAME = "TripTiers Assistant"


async def run_concierge_turn(
    *,
    transcript: str,
    member_count: int,
    known_brief: dict,
    pending_generate_confirmation: bool = False,
) -> ConciergeTurnOutput:
    unresolved = [f for f in FIELD_ORDER if f not in known_brief]
    user = json.dumps(
        {
            "today": today_iso_date(),
            "memberCount": member_count,
            "transcript": transcript,
            "knownBrief": {
                field: {"value": entry.get("value"), "optionLabel": entry.get("optionLabel")}
                for field, entry in known_brief.items()
            },
            "unresolvedFieldsInPriorityOrder": unresolved,
            "fieldLabels": FIELD_LABELS,
            "fieldOptions": FIELD_OPTIONS,
            "pendingGenerateConfirmation": pending_generate_confirmation,
            "instruction": (
                "Find any unresolved fields the transcript clearly answers, check for an explicit correction to "
                "an already-resolved field, decide what to ask next, and check for generate intent/confirmation."
            ),
        },
        indent=2,
    )
    result: ConciergeTurnOutput = await create_structured_output(
        system=CONCIERGE_SYSTEM_PROMPT,
        user=user,
        schema=ConciergeTurnOutput,
        tool_name="emit_concierge_turn",
        timeout_s=TIMEOUT_CLAUDE_CONCIERGE_S,
    )
    log.info(
        "concierge turn",
        resolved=[r.field for r in result.resolved_fields],
        changed_field=result.changed_field,
        should_ask=result.should_ask,
        ask_field=result.ask_field,
        ready=bool(result.ready_message),
        generate_requested=result.generate_requested,
        generate_confirmed=result.generate_confirmed,
    )
    return result
