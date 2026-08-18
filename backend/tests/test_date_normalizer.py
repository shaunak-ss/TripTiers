from datetime import date

from app.validators.date_normalizer import normalize_date_value

_TODAY = date(2026, 8, 17)


def test_iso_passthrough():
    assert normalize_date_value("2026-08-20", today=_TODAY) == ("2026-08-20", "Aug 20, 2026")


def test_slash_formats():
    assert normalize_date_value("20/08/2026", today=_TODAY)[0] == "2026-08-20"
    assert normalize_date_value("08/20/2026", today=_TODAY)[0] == "2026-08-20"


def test_written_month_formats():
    assert normalize_date_value("20 Aug 2026", today=_TODAY)[0] == "2026-08-20"
    assert normalize_date_value("August 20, 2026", today=_TODAY)[0] == "2026-08-20"
    assert normalize_date_value("Aug 20 2026", today=_TODAY)[0] == "2026-08-20"


def test_ordinal_suffix():
    assert normalize_date_value("5th september 2026", today=_TODAY)[0] == "2026-09-05"
    assert normalize_date_value("september 5th, 2026", today=_TODAY)[0] == "2026-09-05"


def test_spelled_out_day_numbers():
    assert normalize_date_value("three august 2026", today=_TODAY)[0] == "2026-08-03"
    assert normalize_date_value("3 august 2026", today=_TODAY)[0] == "2026-08-03"
    assert normalize_date_value("third of august 2026", today=_TODAY)[0] == "2026-08-03"
    assert normalize_date_value("twenty first september 2026", today=_TODAY)[0] == "2026-09-21"
    assert normalize_date_value("twenty-first of september, 2026", today=_TODAY)[0] == "2026-09-21"


def test_no_year_rolls_forward_when_in_past():
    # "Jan 1" with no year, evaluated from Aug 2026, should resolve to next January.
    result = normalize_date_value("Jan 1", today=_TODAY)
    assert result is not None
    assert result[0] == "2027-01-01"


def test_no_year_stays_same_year_when_in_future():
    result = normalize_date_value("Dec 1", today=_TODAY)
    assert result is not None
    assert result[0] == "2026-12-01"


def test_unparseable():
    assert normalize_date_value("", today=_TODAY) is None
    assert normalize_date_value("whenever works", today=_TODAY) is None
    assert normalize_date_value("asdupqwoie", today=_TODAY) is None
