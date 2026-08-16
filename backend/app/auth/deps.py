from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Header

from app.services.supabase_client import get_supabase, get_supabase_anon
from app.utils.errors import AppError


@dataclass
class CurrentUser:
    id: str
    email: str
    name: str
    avatar_hue: int


def _hue_for(user_id: str) -> int:
    return int(hashlib.sha256(user_id.encode()).hexdigest(), 16) % 360


def _display_name(user: Any) -> str:
    meta = getattr(user, "user_metadata", None) or {}
    if isinstance(meta, dict):
        for key in ("full_name", "name", "display_name"):
            value = meta.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    email = getattr(user, "email", None) or ""
    return email.split("@")[0] if email else "Traveler"


def ensure_profile(user_id: str, email: str, name: str) -> dict:
    sb = get_supabase()
    existing = sb.table("profiles").select("*").eq("id", user_id).limit(1).execute()
    if existing.data:
        row = existing.data[0]
        return row
    row = {
        "id": user_id,
        "display_name": name,
        "avatar_hue": _hue_for(user_id),
        "email": email,
    }
    inserted = sb.table("profiles").upsert(row, on_conflict="id").execute()
    return inserted.data[0] if inserted.data else row


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise AppError(
            401,
            "auth_required",
            "Sign in and send Authorization: Bearer <access_token>.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AppError(401, "auth_required", "Sign in and send Authorization: Bearer <access_token>.")

    anon = get_supabase_anon()
    if anon is None:
        raise AppError(503, "auth_unavailable", "SUPABASE_ANON_KEY is not configured on the API.")
    try:
        user_res = anon.auth.get_user(token)
    except Exception as exc:  # noqa: BLE001
        raise AppError(401, "auth_required", "Invalid or expired session.") from exc

    user = getattr(user_res, "user", None)
    if user is None or not getattr(user, "id", None):
        raise AppError(401, "auth_required", "Invalid or expired session.")

    email = getattr(user, "email", None) or ""
    name = _display_name(user)
    profile = ensure_profile(str(user.id), email, name)
    return CurrentUser(
        id=str(user.id),
        email=profile.get("email") or email,
        name=profile.get("display_name") or name,
        avatar_hue=int(profile.get("avatar_hue") or _hue_for(str(user.id))),
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
