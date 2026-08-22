from fastapi import APIRouter, Query

from app.auth.deps import CurrentUserDep, ensure_profile
from app.db.repositories.collab_repository import list_rooms_for_user
from app.db.repositories.trips_repository import list_saved_trips
from app.services.supabase_client import get_supabase
from app.utils.errors import AppError
from app.validators.schemas import CamelModel

router = APIRouter(prefix="/api/me", tags=["me"])


class ProfileUpdateBody(CamelModel):
    display_name: str


@router.get("")
async def me(user: CurrentUserDep) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatarHue": user.avatar_hue,
    }


@router.patch("")
async def update_me(body: ProfileUpdateBody, user: CurrentUserDep) -> dict:
    name = body.display_name.strip()
    if len(name) < 2:
        raise AppError(400, "validation_error", "Name should be at least 2 characters.")
    sb = get_supabase()
    sb.table("profiles").update({"display_name": name}).eq("id", user.id).execute()
    profile = ensure_profile(user.id, user.email, name)
    return {
        "id": user.id,
        "email": profile.get("email") or user.email,
        "name": profile.get("display_name") or name,
        "avatarHue": int(profile.get("avatar_hue") or user.avatar_hue),
    }


@router.get("/trips")
async def my_trips(
    user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
) -> dict:
    return list_saved_trips(user.id, page=page, page_size=page_size)


@router.get("/rooms")
async def my_rooms(
    user: CurrentUserDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
) -> dict:
    return list_rooms_for_user(user.id, page=page, page_size=page_size)
