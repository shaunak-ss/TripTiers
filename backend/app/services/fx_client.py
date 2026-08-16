from __future__ import annotations

import httpx

from app.config import CACHE_TTL_FX, TIMEOUT_FX_S
from app.services.cache_service import cache_get, cache_set
from app.utils.logger import get_logger

log = get_logger(__name__)

FX_API_BASE = "https://api.frankfurter.dev/v1"


def _cache_key(base: str, target: str) -> str:
    return f"fx:{base.upper()}:{target.upper()}"


async def get_fx_rate(base: str, target: str) -> float | None:
    """1 unit of `base` in `target` currency, or None if the rate can't be resolved
    (unsupported currency, network failure) — callers should fall back to `base`."""
    base, target = base.upper(), target.upper()
    if base == target:
        return 1.0

    key = _cache_key(base, target)
    cached = await cache_get(key)
    if isinstance(cached, (int, float)):
        return float(cached)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_FX_S) as client:
            response = await client.get(f"{FX_API_BASE}/latest", params={"from": base, "to": target})
            response.raise_for_status()
            data = response.json()
        rate = data.get("rates", {}).get(target)
        if rate is None:
            log.warning("fx rate unavailable for currency pair", base=base, target=target)
            return None
        await cache_set(key, rate, CACHE_TTL_FX)
        return float(rate)
    except Exception as exc:  # noqa: BLE001
        log.warning("fx rate lookup failed — falling back to base currency", base=base, target=target, error=str(exc))
        return None
