from __future__ import annotations

import json
import time
from typing import Any

import redis.asyncio as redis

from app.config import get_settings
from app.services.supabase_client import get_supabase
from app.utils.logger import get_logger

log = get_logger(__name__)

_memory: dict[str, tuple[Any, float]] = {}
_redis: redis.Redis | None | bool = False


async def _client() -> redis.Redis | None:
    global _redis
    if _redis is False:
        settings = get_settings()
        if settings.redis_url:
            _redis = redis.from_url(settings.redis_url, decode_responses=True)
        else:
            _redis = None
            log.warning("REDIS_URL is not set — using in-memory cache (not shared across instances)")
    return None if _redis is False else _redis


async def cache_get(key: str) -> Any | None:
    client = await _client()
    if client is not None:
        raw = await client.get(key)
        return json.loads(raw) if raw else None
    entry = _memory.get(key)
    if not entry:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        _memory.pop(key, None)
        return None
    return value


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    client = await _client()
    if client is not None:
        await client.set(key, json.dumps(value), ex=ttl_seconds)
        return
    _memory[key] = (value, time.time() + ttl_seconds)


async def get_durable_json(table: str, cache_key: str) -> Any | None:
    sb = get_supabase()
    column = "response" if table == "flight_search_cache" else "days"
    result = sb.table(table).select(f"{column}, expires_at").eq("cache_key", cache_key).limit(1).execute()
    if not result.data:
        return None
    row = result.data[0]
    from datetime import datetime, timezone

    expires = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
    if expires.timestamp() <= datetime.now(timezone.utc).timestamp():
        return None
    return row[column]


async def set_durable_json(table: str, cache_key: str, payload: Any, ttl_seconds: int) -> None:
    from datetime import datetime, timedelta, timezone

    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
    sb = get_supabase()
    row = (
        {"cache_key": cache_key, "response": payload, "expires_at": expires_at}
        if table == "flight_search_cache"
        else {"cache_key": cache_key, "days": payload, "expires_at": expires_at}
    )
    try:
        sb.table(table).upsert(row, on_conflict="cache_key").execute()
    except Exception as exc:  # noqa: BLE001
        log.warning("durable cache write failed", table=table, error=str(exc))
