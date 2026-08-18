from __future__ import annotations

import re

from app.utils.number_words import build_word_number_map, build_word_number_pattern, spell_out_numbers
from app.validators.budget_normalizer import normalize_budget_value
from app.validators.date_normalizer import normalize_date_value

# Spelled-out traveler counts ("four of us", "a party of six") and common
# synonyms for solo/pair trips that don't contain a number at all.
_TRAVELER_WORD_TO_NUMBER = build_word_number_map(40, include_ordinals=False)
_TRAVELER_WORD_PATTERN = build_word_number_pattern(_TRAVELER_WORD_TO_NUMBER)
_TRAVELER_SYNONYMS: dict[str, int] = {
    "solo": 1, "myself": 1, "just me": 1, "alone": 1, "me only": 1,
    "on my own": 1, "by myself": 1, "single": 1,
    "couple": 2, "pair": 2, "both of us": 2, "me and my partner": 2,
}

_TIER_SYNONYMS: dict[str, str] = {
    "backpacking": "backpacker", "budget": "backpacker", "budget travel": "backpacker",
    "shoestring": "backpacker", "cheap": "backpacker", "budget-friendly": "backpacker",
    "mid-range": "comfort", "midrange": "comfort", "mid range": "comfort",
    "standard": "comfort", "moderate": "comfort",
    "luxurious": "luxury", "high-end": "luxury", "high end": "luxury",
    "premium": "luxury", "5-star": "luxury", "five star": "luxury", "lavish": "luxury",
}

_PACE_SYNONYMS: dict[str, str] = {
    "chill": "relaxed", "relaxing": "relaxed", "slow": "relaxed", "easygoing": "relaxed",
    "easy going": "relaxed", "laid back": "relaxed", "laid-back": "relaxed",
    "moderate": "balanced", "medium": "balanced", "normal": "balanced", "mixed": "balanced",
    "busy": "packed", "fast-paced": "packed", "fast paced": "packed", "full": "packed",
    "action-packed": "packed", "action packed": "packed", "jam-packed": "packed",
}

FIELD_ORDER: list[str] = [
    "destination",
    "originCity",
    "startDate",
    "endDate",
    "travelers",
    "budget",
    "tier",
    "pace",
    "dietary",
]

REQUIRED_FIELDS: set[str] = {"destination", "originCity", "startDate", "endDate", "travelers", "budget"}

FIELD_LABELS: dict[str, str] = {
    "destination": "Destination",
    "originCity": "Flying from",
    "startDate": "Start date",
    "endDate": "End date",
    "budget": "Budget",
    "travelers": "Travelers",
    "tier": "Trip style",
    "pace": "Pace",
    "dietary": "Dietary needs",
}

FIELD_OPTIONS: dict[str, list[str]] = {
    "travelers": ["2", "3", "4", "5", "6+"],
    "budget": ["Under $1,000", "$1,000–2,500", "$2,500–5,000", "$5,000+"],
    "tier": ["Backpacker", "Comfort", "Luxury"],
    "pace": ["Relaxed", "Balanced", "Packed"],
    "dietary": ["No restrictions", "Vegetarian", "Vegan", "Halal", "Other"],
}

_OPTION_VALUES: dict[str, dict[str, str]] = {
    "travelers": {"2": "2", "3": "3", "4": "4", "5": "5", "6+": "6"},
    "budget": {
        "Under $1,000": "800",
        "$1,000–2,500": "1750",
        "$2,500–5,000": "3750",
        "$5,000+": "6000",
    },
    "tier": {"Backpacker": "backpacker", "Comfort": "comfort", "Luxury": "luxury"},
    "pace": {"Relaxed": "relaxed", "Balanced": "balanced", "Packed": "packed"},
    "dietary": {
        "No restrictions": "",
        "Vegetarian": "vegetarian",
        "Vegan": "vegan",
        "Halal": "halal",
        "Other": "other",
    },
}


def is_choice_field(field: str) -> bool:
    return field in FIELD_OPTIONS


def normalize_field_value(field: str, raw: str) -> tuple[str, str] | None:
    """Returns (canonicalValue, optionLabel) or None if the raw text can't be parsed
    into a usable value for this field. Handles both an exact tapped chip label and
    a free-text answer the concierge model extracted from chat."""
    raw = (raw or "").strip()
    if not raw:
        return None

    options = _OPTION_VALUES.get(field)
    if options and raw in options:
        return options[raw], raw

    if field == "travelers":
        token = raw.strip().lower()
        n: int | None = None
        if token in _TRAVELER_SYNONYMS:
            n = _TRAVELER_SYNONYMS[token]
        else:
            spelled_out = spell_out_numbers(token, _TRAVELER_WORD_TO_NUMBER, _TRAVELER_WORD_PATTERN)
            # Match an optional leading "-" too, so "-3" is rejected as invalid
            # instead of silently having its sign stripped by a digits-only regex.
            if match := re.search(r"-?\d+", spelled_out):
                n = int(match.group())
        if n is None or n <= 0:
            return None
        return str(n), f"{n} traveler{'s' if n != 1 else ''}"

    if field == "budget":
        parsed = normalize_budget_value(raw)
        if parsed is None:
            return None
        return str(parsed), f"${parsed:,}"

    if field == "tier":
        token = _TIER_SYNONYMS.get(raw.strip().lower(), raw.strip().lower())
        if token not in ("backpacker", "comfort", "luxury"):
            return None
        return token, token.capitalize()

    if field == "pace":
        token = _PACE_SYNONYMS.get(raw.strip().lower(), raw.strip().lower())
        if token not in ("relaxed", "balanced", "packed"):
            return None
        return token, token.capitalize()

    if field == "dietary":
        token = raw.strip().lower()
        if token in ("none", "no restrictions", "n/a", "na"):
            return "", "No restrictions"
        return token, raw.strip()

    if field in ("startDate", "endDate"):
        return normalize_date_value(raw)

    # destination / originCity — free text, taken as-is.
    return raw, raw
