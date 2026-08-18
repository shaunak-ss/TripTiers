import re

from app.utils.number_words import build_word_number_map, build_word_number_pattern, spell_out_numbers

_SCALE_WORDS = {
    "hundred": 100,
    "thousand": 1_000,
    "k": 1_000,
    "l": 100_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
}
_SCALED_RE = re.compile(
    r"^(\d+(?:\.\d+)?)\s*(" + "|".join(sorted(_SCALE_WORDS, key=len, reverse=True)) + r")$"
)
_PLAIN_RE = re.compile(r"^\d+(?:\.\d+)?$")
_CURRENCY_WORDS_RE = re.compile(r"\b(rs\.?|inr|rupees?|usd|dollars?)\b")
_RS_PREFIX_RE = re.compile(r"rs\.?\s*")

# Spelled-out numbers up to 99 cover common idioms like "twenty thousand" or
# "twenty five hundred"; magnitude words themselves (hundred/thousand/lakh/crore)
# are matched literally by _SCALED_RE above, not spelled out.
_WORD_TO_NUMBER = build_word_number_map(99, include_ordinals=False)
_WORD_PATTERN = build_word_number_pattern(_WORD_TO_NUMBER)


def normalize_budget_value(raw: str | int | float) -> int | None:
    """
    Converts free-text or numeric budget input into a clean integer.
    Pure function. No network calls, no LLM calls, no loops that can hang.
    Returns None if input cannot be confidently parsed — caller must show
    a specific inline UI error, never retry this function in a reasoning loop.
    """
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, float)):
        return round(raw) if raw > 0 else None

    s = raw.strip().lower()
    s = re.sub(r"[₹$£€¥,]", "", s)
    s = _RS_PREFIX_RE.sub("", s)
    s = _CURRENCY_WORDS_RE.sub("", s)
    s = s.strip()
    s = spell_out_numbers(s, _WORD_TO_NUMBER, _WORD_PATTERN)

    if m := _SCALED_RE.match(s):
        return round(float(m.group(1)) * _SCALE_WORDS[m.group(2)])
    if _PLAIN_RE.match(s):
        return round(float(s))

    return None
