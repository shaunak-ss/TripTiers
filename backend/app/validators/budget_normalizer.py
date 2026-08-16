import re

_LAKH_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(l|lakh|lakhs)$")
_K_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*k$")
_PLAIN_RE = re.compile(r"^\d+(?:\.\d+)?$")
_CURRENCY_WORDS_RE = re.compile(r"\b(rs\.?|inr|rupees?|usd|dollars?)\b")
_RS_PREFIX_RE = re.compile(r"rs\.?\s*")


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

    if m := _LAKH_RE.match(s):
        return round(float(m.group(1)) * 100_000)
    if m := _K_RE.match(s):
        return round(float(m.group(1)) * 1_000)
    if _PLAIN_RE.match(s):
        return round(float(s))

    return None
