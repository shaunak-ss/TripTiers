from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from app.utils.dates import today_iso_date

TierId = Literal["backpacker", "comfort", "luxury"]


class CamelModel(BaseModel):
    """Write fields in snake_case; serialize JSON as camelCase for the frontend."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        ser_json_by_alias=True,
    )


class TripSearchInput(CamelModel):
    destination: str
    origin_city: str
    start_date: str
    end_date: str
    budget: int
    travelers: int


class TripSearchBody(CamelModel):
    destination: str = Field(min_length=2)
    origin_city: str = Field(min_length=2)
    start_date: str
    end_date: str
    budget: int | float | str
    travelers: int = Field(default=1, ge=1, le=12)

    @field_validator("start_date", "end_date")
    @classmethod
    def _iso_date(cls, value: str) -> str:
        date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def _date_rules(self) -> "TripSearchBody":
        today = today_iso_date()
        if self.start_date < today:
            raise ValueError("Start date cannot be in the past.")
        if self.end_date <= self.start_date:
            raise ValueError("Return date must be after departure.")
        return self


class FlightLeg(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    from_: str = Field(alias="from")
    to: str
    carrier: str


class FlightOption(CamelModel):
    airline: str
    legs: list[FlightLeg]
    price: int
    duration_minutes: int
    booking_url: str


class ItineraryDay(CamelModel):
    day: int
    title: str
    morning: str
    afternoon: str
    evening: str


class Stay(CamelModel):
    name: str
    type: str
    price_per_night: int
    booking_url: str


class TripTier(CamelModel):
    tier: TierId
    total_price: int
    flight: FlightOption
    stay: Stay
    highlights: list[str]
    itinerary: list[ItineraryDay]


class TripResult(CamelModel):
    trip_id: str
    input: TripSearchInput
    tiers: list[TripTier]
    generated_at: str
    currency: str = "USD"


class TieringDraft(CamelModel):
    tier: TierId
    stay_name: str
    stay_type: str
    highlights: list[str] = Field(min_length=3, max_length=4)


class TieringAgentOutput(CamelModel):
    budget_warning: str | None = None
    tiers: list[TieringDraft]


class ItineraryAgentOutput(CamelModel):
    days: list[ItineraryDay]


class Attraction(BaseModel):
    name: str
    area: str | None = None
    note: str | None = None
    suggested_duration_minutes: int | None = Field(default=None, alias="suggestedDurationMinutes")

    model_config = ConfigDict(populate_by_name=True)


class Neighborhood(BaseModel):
    name: str
    vibe: str | None = None


class StayIdeas(BaseModel):
    backpacker: list[str] = Field(default_factory=list)
    comfort: list[str] = Field(default_factory=list)
    luxury: list[str] = Field(default_factory=list)


class CuratedFacts(BaseModel):
    attractions: list[Attraction] = Field(default_factory=list)
    neighborhoods: list[Neighborhood] = Field(default_factory=list)
    local_tips: list[str] = Field(default_factory=list, alias="localTips")
    stay_ideas: StayIdeas | None = Field(default=None, alias="stayIdeas")

    model_config = ConfigDict(populate_by_name=True)


class DestinationFacts(BaseModel):
    slug: str
    city: str
    country: str
    cost_index: float
    currency_code: str = "USD"
    curated_facts: CuratedFacts
    source: str = "manual"


class DestinationFactsAgentOutput(CamelModel):
    city: str
    country: str
    cost_index: float = Field(
        description="Relative daily travel cost vs. a US mid-size city baseline of 1.0 (e.g. 0.6 = notably cheaper, 1.8 = notably pricier)."
    )
    currency_code: str = Field(description="ISO 4217 currency code used in this destination, e.g. INR, JPY, EUR.")
    attractions: list[Attraction] = Field(min_length=4, max_length=8)
    neighborhoods: list[Neighborhood] = Field(min_length=2, max_length=4)
    local_tips: list[str] = Field(min_length=2, max_length=5)
    stay_ideas: StayIdeas


class HotelCostEstimate(BaseModel):
    destination_slug: str
    tier: TierId
    price_per_night: int
    currency: str
    type: str
    suggested_names: list[str]
    booking_url: str


class CollabChatMessage(CamelModel):
    display_name: str
    body: str
    created_at: str | None = None


class CollabGenerateBody(CamelModel):
    room_code: str = ""
    member_count: int = Field(default=1, ge=1, le=12)
    messages: list[CollabChatMessage] = Field(min_length=1)


class CollabExtractOutput(CamelModel):
    destination: str = ""
    origin_city: str = ""
    start_date: str = ""
    end_date: str = ""
    budget: int = 0
    travelers: int = 1
    notes: str = ""
    missing_fields: list[str] = Field(default_factory=list)


def tool_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema.pop("$schema", None)
    schema.pop("title", None)
    return schema
