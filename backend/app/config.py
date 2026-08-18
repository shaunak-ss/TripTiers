from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TierId = Literal["backpacker", "comfort", "luxury"]

TIER_ORDER: tuple[TierId, ...] = ("backpacker", "comfort", "luxury")

STAY_TYPE: dict[str, str] = {
    "backpacker": "Hostel / guesthouse",
    "comfort": "3–4 star hotel",
    "luxury": "5 star hotel / resort",
}

HOTEL_BASE_NIGHTLY: dict[str, dict[str, int]] = {
    "USD": {"backpacker": 28, "comfort": 95, "luxury": 280},
    "INR": {"backpacker": 1800, "comfort": 7500, "luxury": 22000},
}

DAILY_SPEND_BASE: dict[str, dict[str, int]] = {
    "USD": {"backpacker": 25, "comfort": 55, "luxury": 140},
    "INR": {"backpacker": 900, "comfort": 2200, "luxury": 6500},
}

PRICE_TOLERANCE_UNDER = 0.9
PRICE_TOLERANCE_OVER = 1.25

TIMEOUT_KIWI_S = 4.0
TIMEOUT_CLAUDE_TIERING_S = 14.0
TIMEOUT_CLAUDE_ITINERARY_S = 12.0
TIMEOUT_CLAUDE_FACTS_S = 25.0
TIMEOUT_CLAUDE_COLLAB_S = 16.0
TIMEOUT_CLAUDE_CONCIERGE_S = 12.0

CACHE_TTL_FLIGHTS = 20 * 60
CACHE_TTL_FLIGHTS_DURABLE = 24 * 60 * 60
CACHE_TTL_ITINERARY = 24 * 60 * 60
CACHE_TTL_ITINERARY_PERSONALIZED = 15 * 60
CACHE_TTL_DESTINATION = 6 * 60 * 60
CACHE_TTL_LOCATION = 7 * 24 * 60 * 60
CACHE_TTL_FX = 6 * 60 * 60
TIMEOUT_FX_S = 4.0

CITY_IATA: dict[str, str] = {
    "new delhi": "DEL",
    "delhi": "DEL",
    "mumbai": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "hyderabad": "HYD",
    "chennai": "MAA",
    "kolkata": "CCU",
    "london": "LON",
    "new york": "NYC",
    "nyc": "NYC",
    "singapore": "SIN",
    "dubai": "DXB",
    "paris": "PAR",
    "tokyo": "TYO",
    "bali": "DPS",
    "ubud": "DPS",
    "lisbon": "LIS",
    "bangkok": "BKK",
    "santorini": "JTR",
    "new york, usa": "NYC",
    "bali, indonesia": "DPS",
    "tokyo, japan": "TYO",
    "lisbon, portugal": "LIS",
    "paris, france": "PAR",
    "bangkok, thailand": "BKK",
    "santorini, greece": "JTR",
    "dubai, uae": "DXB",
}


_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PLACEHOLDER_KEYS = {"", "YOUR_KIWI_API_KEY", "changeme"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    port: int = 3001
    log_level: str = "info"
    cors_origin: str = "http://localhost:5173"
    app_currency: Literal["USD", "INR"] = "USD"

    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str | None = None

    gemini_api_key: str
    gemini_model: str = "gemini-flash-lite-latest"

    kiwi_api_key: str | None = None
    kiwi_api_base: str = "https://api.tequila.kiwi.com"
    kiwi_mock: bool = False

    redis_url: str | None = None

    @field_validator("kiwi_api_key", "redis_url", "supabase_anon_key", mode="before")
    @classmethod
    def _empty_str_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _require_integrations(self) -> "Settings":
        if self.environment == "production" and not self.use_kiwi_mock and not self.kiwi_api_key:
            raise ValueError("KIWI_API_KEY is required unless KIWI_MOCK=true.")
        if self.environment == "production" and not self.redis_url:
            raise ValueError("REDIS_URL is required when ENVIRONMENT=production.")
        return self

    @property
    def use_kiwi_mock(self) -> bool:
        key = (self.kiwi_api_key or "").strip()
        return self.kiwi_mock or key in _PLACEHOLDER_KEYS

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origin.split(",") if origin.strip()]

    @property
    def redis_configured(self) -> bool:
        return bool(self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def cache_key_flights(origin: str, dest: str, start: str, end: str) -> str:
    return f"flights:{origin.lower()}:{dest.lower()}:{start}:{end}"


def cache_key_itinerary(slug: str, tier: str, days: int) -> str:
    return f"itinerary:{slug}:{tier}:{days}"


def cache_key_itinerary_personalized(slug: str, tier: str, days: int, preferences_hash: str) -> str:
    return f"itinerary:personalized:{slug}:{tier}:{days}:{preferences_hash}"


def cache_key_destination(slug: str) -> str:
    return f"destination:{slug}"


def cache_key_location(query: str) -> str:
    return f"location:{query.lower().strip()}"
