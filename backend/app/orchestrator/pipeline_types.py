from dataclasses import dataclass

from app.validators.schemas import DestinationFacts, FlightOption, HotelCostEstimate, TierId


@dataclass
class PipelineContext:
    destination: DestinationFacts
    flight: FlightOption
    stays: dict[TierId, HotelCostEstimate]
    daily_spend: dict[TierId, int]
    days: int
    nights: int
