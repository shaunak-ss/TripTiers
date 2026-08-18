import pytest

from app.services.trip_brief_fields import FIELD_ORDER, normalize_field_value

# --- destination / originCity: free text, always passed through as-is. ---


@pytest.mark.parametrize("field", ["destination", "originCity"])
@pytest.mark.parametrize(
    "raw,expected_value",
    [
        ("Thailand", "Thailand"),
        ("  Bali, Indonesia  ", "Bali, Indonesia"),
        ("New York City", "New York City"),
    ],
)
def test_free_text_fields(field, raw, expected_value):
    result = normalize_field_value(field, raw)
    assert result is not None
    assert result[0] == expected_value


# --- travelers ---


@pytest.mark.parametrize(
    "raw,expected_n",
    [
        ("2", 2),
        (" 4 ", 4),
        ("six", 6),
        ("four people", 4),
        ("a party of six", 6),
        ("family of 5", 5),
        ("family of four", 4),
        ("two of us", 2),
        ("solo", 1),
        ("just me", 1),
        ("myself", 1),
        ("alone", 1),
        ("couple", 2),
        ("pair", 2),
        ("both of us", 2),
        ("6+", 6),  # exact chip label
    ],
)
def test_travelers_valid(raw, expected_n):
    result = normalize_field_value("travelers", raw)
    assert result is not None, f"expected {raw!r} to resolve to {expected_n} travelers"
    assert result[0] == str(expected_n)


@pytest.mark.parametrize("raw", ["", "no idea", "0", "-3", "many"])
def test_travelers_invalid(raw):
    assert normalize_field_value("travelers", raw) is None


# --- budget ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2000", 2000),
        ("$2,000", 2000),
        ("20k", 20000),
        ("1.5 lakh", 150000),
        ("₹50000", 50000),
        ("two thousand", 2000),
        ("twenty thousand", 20000),
        ("twenty five hundred", 2500),
        ("one lakh", 100000),
        ("Under $1,000", 800),  # exact chip label
    ],
)
def test_budget_valid(raw, expected):
    result = normalize_field_value("budget", raw)
    assert result is not None, f"expected {raw!r} to resolve to {expected}"
    assert result[0] == str(expected)


@pytest.mark.parametrize("raw", ["", "idk", "around twenty thousand"])
def test_budget_invalid(raw):
    assert normalize_field_value("budget", raw) is None


# --- tier ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("backpacker", "backpacker"),
        ("Comfort", "comfort"),
        ("LUXURY", "luxury"),
        ("backpacking", "backpacker"),
        ("budget travel", "backpacker"),
        ("mid-range", "comfort"),
        ("high-end", "luxury"),
        ("premium", "luxury"),
        ("Luxury", "luxury"),  # exact chip label
    ],
)
def test_tier_valid(raw, expected):
    result = normalize_field_value("tier", raw)
    assert result is not None, f"expected {raw!r} to resolve to {expected}"
    assert result[0] == expected


@pytest.mark.parametrize("raw", ["", "whatever works", "fancy but cheap"])
def test_tier_invalid(raw):
    assert normalize_field_value("tier", raw) is None


# --- pace ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("relaxed", "relaxed"),
        ("Balanced", "balanced"),
        ("PACKED", "packed"),
        ("chill", "relaxed"),
        ("laid-back", "relaxed"),
        ("moderate", "balanced"),
        ("busy", "packed"),
        ("action-packed", "packed"),
        ("Relaxed", "relaxed"),  # exact chip label
    ],
)
def test_pace_valid(raw, expected):
    result = normalize_field_value("pace", raw)
    assert result is not None, f"expected {raw!r} to resolve to {expected}"
    assert result[0] == expected


@pytest.mark.parametrize("raw", ["", "whenever", "sometimes fast sometimes slow"])
def test_pace_invalid(raw):
    assert normalize_field_value("pace", raw) is None


# --- dietary ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("vegetarian", "vegetarian"),
        ("Vegan", "vegan"),
        ("none", ""),
        ("no restrictions", ""),
        ("n/a", ""),
        ("No restrictions", ""),  # exact chip label
    ],
)
def test_dietary(raw, expected):
    result = normalize_field_value("dietary", raw)
    assert result is not None
    assert result[0] == expected


# --- startDate / endDate ---


@pytest.mark.parametrize("field", ["startDate", "endDate"])
@pytest.mark.parametrize(
    "raw,expected_iso",
    [
        ("2026-08-20", "2026-08-20"),
        ("20/08/2026", "2026-08-20"),
        ("20 Aug 2026", "2026-08-20"),
        ("August 20, 2026", "2026-08-20"),
        ("three august 2026", "2026-08-03"),
        ("3 august 2026", "2026-08-03"),
    ],
)
def test_dates_valid(field, raw, expected_iso):
    result = normalize_field_value(field, raw)
    assert result is not None, f"expected {raw!r} to resolve to {expected_iso}"
    assert result[0] == expected_iso


@pytest.mark.parametrize("field", ["startDate", "endDate"])
def test_dates_invalid(field):
    assert normalize_field_value(field, "") is None
    assert normalize_field_value(field, "whenever works") is None


def test_field_order_is_stable_and_covers_all_known_fields():
    assert FIELD_ORDER == [
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
