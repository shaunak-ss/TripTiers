from __future__ import annotations

import re

from app.validators.budget_normalizer import normalize_budget_value

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
        match = re.search(r"\d+", raw)
        if not match:
            return None
        n = int(match.group())
        if n <= 0:
            return None
        return str(n), f"{n} traveler{'s' if n != 1 else ''}"

    if field == "budget":
        parsed = normalize_budget_value(raw)
        if parsed is None:
            return None
        return str(parsed), f"${parsed:,}"

    if field == "tier":
        token = raw.strip().lower()
        if token not in ("backpacker", "comfort", "luxury"):
            return None
        return token, token.capitalize()

    if field == "pace":
        token = raw.strip().lower()
        if token not in ("relaxed", "balanced", "packed"):
            return None
        return token, token.capitalize()

    if field == "dietary":
        token = raw.strip().lower()
        if token in ("none", "no restrictions", "n/a", "na"):
            return "", "No restrictions"
        return token, raw.strip()

    # destination / originCity / startDate / endDate — free text, taken as-is.
    return raw, raw
