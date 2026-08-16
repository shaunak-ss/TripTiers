from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.auth.deps import CurrentUserDep
from app.db.repositories.trips_repository import get_trip_result, save_trip
from app.orchestrator.trip_pipeline import run_trip_pipeline
from app.utils.errors import AppError
from app.validators.budget_normalizer import normalize_budget_value
from app.validators.schemas import TripResult, TripSearchBody, TripSearchInput

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("", response_model=TripResult, response_model_by_alias=True)
async def create_trip(body: TripSearchBody) -> TripResult:
    budget = normalize_budget_value(body.budget)
    if budget is None:
        raise AppError(400, "budget_unparseable", "Try a plain number, like 20000 or 20k.")
    payload = TripSearchInput(
        destination=body.destination,
        origin_city=body.origin_city,
        start_date=body.start_date,
        end_date=body.end_date,
        budget=budget,
        travelers=body.travelers,
    )
    return await run_trip_pipeline(payload, str(body.budget))


@router.get("/{trip_id}", response_model_by_alias=True)
async def get_trip(trip_id: str):
    found = get_trip_result(trip_id)
    if found is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Trip not found."})
    if found["status"] == "pending":
        return {"status": "pending"}
    if found["status"] == "failed":
        raise HTTPException(
            status_code=409,
            detail={"error": "trip_failed", "message": "This trip failed to generate. Start a new search."},
        )
    return JSONResponse(content=found["result"].model_dump(by_alias=True, mode="json"))


@router.post("/{trip_id}/save")
async def save_trip_endpoint(trip_id: str, user: CurrentUserDep) -> dict[str, bool]:
    existing = get_trip_result(trip_id)
    if existing is None:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Trip not found."})
    save_trip(user.id, trip_id)
    return {"saved": True}
