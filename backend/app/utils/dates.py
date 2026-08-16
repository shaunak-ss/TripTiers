from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    return date.fromisoformat(value)


def trip_length_days(start_iso: str, end_iso: str) -> int:
    start = parse_iso_date(start_iso)
    end = parse_iso_date(end_iso)
    return max(1, (end - start).days + 1)


def trip_length_nights(start_iso: str, end_iso: str) -> int:
    start = parse_iso_date(start_iso)
    end = parse_iso_date(end_iso)
    return max(0, (end - start).days)


def to_kiwi_date(iso: str) -> str:
    year, month, day = iso.split("-")
    return f"{day}/{month}/{year}"


def today_iso_date() -> str:
    return datetime.utcnow().date().isoformat()
