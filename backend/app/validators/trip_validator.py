from dataclasses import dataclass

from app.config import DAILY_SPEND_BASE, PRICE_TOLERANCE_OVER, PRICE_TOLERANCE_UNDER, TIER_ORDER, get_settings
from app.validators.schemas import TripResult


@dataclass
class ValidationIssue:
    message: str
    tier: str | None = None


def validate_trip_result(result: TripResult, days: int, nights: int, fx_rate: float = 1.0) -> list[ValidationIssue]:
    settings = get_settings()
    issues: list[ValidationIssue] = []

    if not result.tiers:
        issues.append(ValidationIssue("No tiers produced."))
        return issues

    for tier in result.tiers:
        if len(tier.itinerary) != days:
            issues.append(
                ValidationIssue(f"Itinerary has {len(tier.itinerary)} days, expected {days}.", tier.tier)
            )

        seen: set[int] = set()
        for day in tier.itinerary:
            if day.day in seen:
                issues.append(ValidationIssue(f"Duplicate day {day.day}.", tier.tier))
            seen.add(day.day)
            if not day.title.strip() or not day.morning.strip() or not day.afternoon.strip() or not day.evening.strip():
                issues.append(ValidationIssue(f"Day {day.day} has an empty field.", tier.tier))

        stay_total = tier.stay.price_per_night * nights
        expected_min = tier.flight.price + stay_total
        daily = DAILY_SPEND_BASE[settings.app_currency][tier.tier] * fx_rate
        expected_max = expected_min + daily * days * 4

        if tier.total_price < expected_min * PRICE_TOLERANCE_UNDER:
            issues.append(
                ValidationIssue(
                    f"totalPrice {tier.total_price} is below flight+stay baseline {expected_min}.",
                    tier.tier,
                )
            )
        if tier.total_price > expected_max * PRICE_TOLERANCE_OVER:
            issues.append(
                ValidationIssue(
                    f"totalPrice {tier.total_price} is far above flight+stay+buffer {expected_max}.",
                    tier.tier,
                )
            )

    missing = [tid for tid in TIER_ORDER if not any(t.tier == tid for t in result.tiers)]
    if missing:
        issues.append(ValidationIssue(f"Missing tiers: {', '.join(missing)}"))

    return issues
