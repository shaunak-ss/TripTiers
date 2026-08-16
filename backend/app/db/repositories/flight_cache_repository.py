from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.supabase_client import get_supabase
from app.utils.logger import get_logger
from app.validators.schemas import FlightOption

log = get_logger(__name__)


def get_flight_cache(cache_key: str, *, allow_expired: bool = False) -> list[dict] | None:
    sb = get_supabase()
    result = sb.table("flight_search_cache").select("response, expires_at").eq("cache_key", cache_key).limit(1).execute()
    if not result.data:
        return None
    row = result.data[0]
    expires = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
    if expires.timestamp() <= datetime.now(timezone.utc).timestamp() and not allow_expired:
        return None
    return row["response"]


def set_flight_cache(cache_key: str, flights: list[FlightOption], ttl_seconds: int) -> None:
    sb = get_supabase()
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
    payload = {
        "cache_key": cache_key,
        "response": [f.model_dump(by_alias=True) for f in flights],
        "expires_at": expires_at,
    }
    try:
        sb.table("flight_search_cache").upsert(payload, on_conflict="cache_key").execute()
    except Exception as exc:  # noqa: BLE001
        log.warning("flight cache write failed", error=str(exc))
