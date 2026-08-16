from app.config import CACHE_TTL_DESTINATION, cache_key_destination
from app.db.repositories.destinations_repository import bootstrap_destination, find_destination
from app.services.cache_service import cache_get, cache_set
from app.utils.logger import get_logger
from app.validators.schemas import DestinationFacts

log = get_logger(__name__)


async def get_destination_facts(destination_slug: str) -> DestinationFacts:
    key = cache_key_destination(destination_slug)
    cached = await cache_get(key)
    if cached:
        return DestinationFacts.model_validate(cached)

    row = find_destination(destination_slug)
    if row is None:
        log.info("destination miss — bootstrapping", query=destination_slug)
        row = await bootstrap_destination(destination_slug)

    await cache_set(key, row.model_dump(by_alias=True), CACHE_TTL_DESTINATION)
    return row
