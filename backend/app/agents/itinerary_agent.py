from __future__ import annotations

import hashlib
import json

from app.config import (
    CACHE_TTL_ITINERARY,
    CACHE_TTL_ITINERARY_PERSONALIZED,
    TIMEOUT_CLAUDE_ITINERARY_S,
    cache_key_itinerary,
    cache_key_itinerary_personalized,
)
from app.prompts import ITINERARY_SYSTEM_PROMPT
from app.services.cache_service import cache_get, cache_set, get_durable_json, set_durable_json
from app.services.gemini_client import create_structured_output
from app.utils.logger import get_logger
from app.validators.schemas import DestinationFacts, ItineraryAgentOutput, ItineraryDay, TierId

log = get_logger(__name__)


def fallback_itinerary(destination: DestinationFacts, days: int, tier: TierId) -> list[ItineraryDay]:
    attractions = destination.curated_facts.attractions
    neighborhoods = destination.curated_facts.neighborhoods
    tips = destination.curated_facts.local_tips
    out: list[ItineraryDay] = []
    for i in range(days):
        day = i + 1
        attraction = attractions[i % len(attractions)] if attractions else None
        neighborhood = neighborhoods[i % len(neighborhoods)] if neighborhoods else None
        place = attraction.name if attraction else f"{destination.city} center"
        area = neighborhood.name if neighborhood else destination.city
        if day == 1:
            out.append(
                ItineraryDay(
                    day=day,
                    title=f"Arrive and settle into {area}",
                    morning=f"Land, transfer to your {tier} stay in {area}, and drop your bags.",
                    afternoon=f"Take a short orientation walk so the streets around {area} make sense.",
                    evening=tips[0] if tips else "Keep dinner close to your stay on arrival night.",
                )
            )
        elif day == days:
            out.append(
                ItineraryDay(
                    day=day,
                    title=f"Last looks at {destination.city}",
                    morning=f"A lighter morning near {place} if time allows before checkout.",
                    afternoon="Buffer time for the airport run — don't schedule a distant outing.",
                    evening="Depart. Leave extra time for traffic and security.",
                )
            )
        else:
            note = f" — {attraction.note}" if attraction and attraction.note else "."
            vibe = f" ({neighborhood.vibe})" if neighborhood and neighborhood.vibe else "."
            evening = tips[i % len(tips)] if tips else f"Eat in {area} and turn in at a reasonable hour."
            out.append(
                ItineraryDay(
                    day=day,
                    title=place,
                    morning=f"Head to {place}{note}",
                    afternoon=f"Stay in {area} and keep the afternoon unhurried{vibe}",
                    evening=evening,
                )
            )
    return out


async def _generate(
    destination: DestinationFacts, tier: TierId, days: int, preferences_text: str | None = None
) -> list[ItineraryDay]:
    payload: dict[str, object] = {
        "destination": f"{destination.city}, {destination.country}",
        "tier": tier,
        "tripLengthDays": days,
        "instruction": f"Return exactly {days} days. Only use names from the destination facts block.",
    }
    if preferences_text:
        payload["groupPreferences"] = preferences_text
    user = json.dumps(payload, indent=2)
    facts_block = {
        "type": "text",
        "text": "DESTINATION FACTS (only cite names that appear here):\n"
        + json.dumps(destination.curated_facts.model_dump(by_alias=True), indent=2),
        "cache_control": {"type": "ephemeral"},
    }
    result: ItineraryAgentOutput = await create_structured_output(
        system=ITINERARY_SYSTEM_PROMPT,
        user=user,
        schema=ItineraryAgentOutput,
        tool_name="emit_itinerary",
        timeout_s=TIMEOUT_CLAUDE_ITINERARY_S,
        extra_cached_blocks=[facts_block],
    )
    return result.days


async def run_itinerary_agent(
    *,
    destination: DestinationFacts,
    tier: TierId,
    days: int,
    preferences_text: str | None = None,
) -> tuple[list[ItineraryDay], bool, bool]:
    personalized = bool(preferences_text and preferences_text.strip())

    if personalized:
        prefs_hash = hashlib.sha1(preferences_text.strip().encode("utf-8")).hexdigest()[:16]  # noqa: S324
        key = cache_key_itinerary_personalized(destination.slug, tier, days, prefs_hash)
        ttl = CACHE_TTL_ITINERARY_PERSONALIZED
    else:
        key = cache_key_itinerary(destination.slug, tier, days)
        ttl = CACHE_TTL_ITINERARY

    hot = await cache_get(key)
    if isinstance(hot, list) and len(hot) == days:
        log.info("itinerary skeleton cache hit (redis)", key=key, personalized=personalized)
        return [ItineraryDay.model_validate(d) for d in hot], True, False

    if not personalized:
        # The shared, cross-user durable skeleton cache only applies to generic (non-personalized) plans.
        durable = await get_durable_json("itinerary_skeleton_cache", key)
        if isinstance(durable, list) and len(durable) == days:
            log.info("itinerary skeleton cache hit (postgres)", key=key)
            days_models = [ItineraryDay.model_validate(d) for d in durable]
            await cache_set(key, [d.model_dump() for d in days_models], ttl)
            return days_models, True, False

    try:
        generated = await _generate(destination, tier, days, preferences_text)
        if len(generated) != days:
            log.warning("itinerary day count mismatch — retrying once", got=len(generated), expected=days, tier=tier)
            generated = await _generate(destination, tier, days, preferences_text)
        if len(generated) == days:
            payload = [d.model_dump() for d in generated]
            await cache_set(key, payload, ttl)
            if not personalized:
                await set_durable_json("itinerary_skeleton_cache", key, payload, ttl)
            return generated, False, False
    except Exception as exc:  # noqa: BLE001
        log.error("itinerary agent failed — using facts fallback", tier=tier, error=str(exc))

    return fallback_itinerary(destination, days, tier), False, True
