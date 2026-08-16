import re


def slugify_destination(value: str) -> str:
    slug = value.strip().lower().replace("&", " and ")
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def parse_destination_name(value: str) -> tuple[str, str, str]:
    trimmed = value.strip()
    parts = [p.strip() for p in trimmed.split(",") if p.strip()]
    city = parts[0] if parts else trimmed
    country = ", ".join(parts[1:]) if len(parts) > 1 else "Unknown"
    return city, country, slugify_destination(trimmed)
