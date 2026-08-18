from __future__ import annotations

import re
from datetime import date, datetime, time, timedelta

from dateutil import parser as _date_parser
from dateutil.parser import ParserError

from app.utils.number_words import build_word_number_map, build_word_number_pattern, spell_out_numbers

_YEAR_RE = re.compile(r"\b\d{4}\b")

_WORD_TO_NUMBER = build_word_number_map(31, include_ordinals=True)
_WORD_PATTERN = build_word_number_pattern(_WORD_TO_NUMBER)


def _spell_out_day_numbers(text: str) -> str:
    """dateutil's fuzzy mode silently *drops* number words it doesn't recognize (e.g.
    "three august 2026" quietly becomes today's day-of-month instead of the 3rd) rather
    than failing — confidently wrong, not just unparsed. Converting spelled-out day
    numbers ("three", "third", "twenty-first"...) to digits before parsing avoids that."""
    return spell_out_numbers(text, _WORD_TO_NUMBER, _WORD_PATTERN)


def _label(value: date) -> str:
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def normalize_date_value(raw: str, *, today: date | None = None) -> tuple[str, str] | None:
    """
    Converts free-text or already-ISO date input into a clean 'YYYY-MM-DD' string.
    Pure function. No network calls, no LLM calls, no loops that can hang.

    Handles ISO dates, common written/numeric formats regardless of day/month order
    ("20/08/2026", "08/20/2026", "20 Aug 2026", "August 20, 2026", "5th september"),
    and a bare month/day with no year (assumed to be the next upcoming occurrence —
    trips are always in the future). Doesn't resolve relative phrases like "next
    Monday" — that needs live "today" context and is left to the LLM upstream; this
    is the deterministic safety net that runs on whatever the LLM (or a user typing a
    date directly) actually produces.

    Returns None if input cannot be confidently parsed — caller must show a specific
    inline error, never retry this function in a reasoning loop.
    """
    raw = (raw or "").strip()
    if not raw:
        return None

    today = today or datetime.utcnow().date()

    try:
        parsed = date.fromisoformat(raw)
        return parsed.isoformat(), _label(parsed)
    except ValueError:
        pass

    had_year = bool(_YEAR_RE.search(raw))
    spelled_out = _spell_out_day_numbers(raw)
    try:
        parsed_dt = _date_parser.parse(
            spelled_out, dayfirst=False, fuzzy=True, default=datetime.combine(today, time.min)
        )
    except (ParserError, ValueError, OverflowError, TypeError):
        return None

    parsed = parsed_dt.date()
    if not had_year and parsed < today:
        try:
            parsed = parsed.replace(year=parsed.year + 1)
        except ValueError:
            parsed = parsed + timedelta(days=365)

    return parsed.isoformat(), _label(parsed)
