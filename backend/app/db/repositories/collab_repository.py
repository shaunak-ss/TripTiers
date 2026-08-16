from __future__ import annotations

import secrets
from datetime import datetime, timezone

from app.services.supabase_client import get_supabase
from app.utils.logger import get_logger

log = get_logger(__name__)
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_room_code() -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(6))


def _assemble(room: dict, members: list[dict], messages: list[dict]) -> dict:
    return {
        "id": room["id"],
        "code": room["code"],
        "name": room["name"],
        "tripId": room.get("trip_id"),
        "generatedTripId": room.get("generated_trip_id"),
        "hostUserId": str(room["host_user_id"]),
        "createdAt": room.get("created_at") or _now(),
        "members": [
            {
                "userId": str(row["user_id"]),
                "displayName": row["display_name"],
                "email": row.get("email"),
                "joinedAt": row.get("joined_at") or _now(),
            }
            for row in members
        ],
        "messages": [
            {
                "id": row["id"],
                "roomId": row["room_id"],
                "userId": str(row["user_id"]),
                "displayName": row["display_name"],
                "body": row["body"],
                "createdAt": row.get("created_at") or _now(),
            }
            for row in messages
        ],
    }


def _load(room: dict) -> dict:
    sb = get_supabase()
    members = sb.table("collab_members").select("*").eq("room_id", room["id"]).execute()
    messages = (
        sb.table("collab_messages").select("*").eq("room_id", room["id"]).order("created_at").execute()
    )
    return _assemble(room, members.data or [], messages.data or [])


def get_room_by_code(code: str) -> dict | None:
    rooms = get_supabase().table("collab_rooms").select("*").eq("code", code.upper()).limit(1).execute()
    if not rooms.data:
        return None
    return _load(rooms.data[0])


def assert_member(room: dict, user_id: str) -> None:
    if not any(member["userId"] == user_id for member in room["members"]):
        raise PermissionError("not_a_member")


def list_rooms_for_user(user_id: str) -> list[dict]:
    sb = get_supabase()
    memberships = sb.table("collab_members").select("room_id").eq("user_id", user_id).execute()
    rooms: list[dict] = []
    seen: set[str] = set()
    for row in memberships.data or []:
        room_id = row["room_id"]
        if room_id in seen:
            continue
        seen.add(room_id)
        found = sb.table("collab_rooms").select("*").eq("id", room_id).limit(1).execute()
        if found.data:
            rooms.append(_load(found.data[0]))
    rooms.sort(key=lambda item: item["createdAt"], reverse=True)
    return rooms


def create_room(
    *,
    name: str,
    host_user_id: str,
    display_name: str,
    email: str | None,
    trip_id: str | None,
) -> dict:
    sb = get_supabase()
    last_error: Exception | None = None
    for _ in range(6):
        code = new_room_code()
        try:
            inserted = sb.table("collab_rooms").insert(
                {
                    "code": code,
                    "name": name,
                    "trip_id": trip_id,
                    "host_user_id": host_user_id,
                }
            ).execute()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue
        if not inserted.data:
            continue
        room = inserted.data[0]
        sb.table("collab_members").insert(
            {
                "room_id": room["id"],
                "user_id": host_user_id,
                "display_name": display_name,
                "email": email,
            }
        ).execute()
        return get_room_by_code(code) or _assemble(room, [], [])
    raise RuntimeError(f"Failed to create room: {last_error}")


def join_room(*, code: str, user_id: str, display_name: str, email: str | None) -> dict:
    room = get_room_by_code(code)
    if room is None:
        raise KeyError("room_not_found")
    if any(member["userId"] == user_id for member in room["members"]):
        return room
    get_supabase().table("collab_members").insert(
        {
            "room_id": room["id"],
            "user_id": user_id,
            "display_name": display_name,
            "email": email,
        }
    ).execute()
    return get_room_by_code(code) or room


def add_message(*, code: str, user_id: str, display_name: str, body: str) -> dict:
    room = get_room_by_code(code)
    if room is None:
        raise KeyError("room_not_found")
    assert_member(room, user_id)
    inserted = get_supabase().table("collab_messages").insert(
        {
            "room_id": room["id"],
            "user_id": user_id,
            "display_name": display_name,
            "body": body,
        }
    ).execute()
    if not inserted.data:
        raise RuntimeError("Failed to post message")
    row = inserted.data[0]
    return {
        "id": row["id"],
        "roomId": row["room_id"],
        "userId": str(row["user_id"]),
        "displayName": row["display_name"],
        "body": row["body"],
        "createdAt": row.get("created_at") or _now(),
    }


def set_generated_trip(code: str, trip_id: str) -> None:
    get_supabase().table("collab_rooms").update({"generated_trip_id": trip_id}).eq("code", code.upper()).execute()
