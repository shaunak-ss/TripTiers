from datetime import datetime, timezone

from app.db.seed_data import SEED_DESTINATIONS
from app.services.supabase_client import get_supabase
from app.utils.logger import configure_logging, get_logger

log = get_logger(__name__)


def main() -> None:
    configure_logging("info")
    sb = get_supabase()
    for dest in SEED_DESTINATIONS:
        payload = {
            "slug": dest["slug"],
            "city": dest["city"],
            "country": dest["country"],
            "cost_index": dest["cost_index"],
            "currency_code": dest.get("currency_code", "USD"),
            "curated_facts": dest["facts"],
            "source": "manual",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        error = None
        try:
            sb.table("destinations").upsert(payload, on_conflict="slug").execute()
        except Exception as exc:  # noqa: BLE001
            error = exc
        if error:
            log.error("seed failed", slug=dest["slug"], error=str(error))
            raise error
        log.info("seeded destination", slug=dest["slug"])
    log.info("seed complete", count=len(SEED_DESTINATIONS))


if __name__ == "__main__":
    main()
