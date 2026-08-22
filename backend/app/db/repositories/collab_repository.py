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


def _message_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "roomId": row["room_id"],
        "userId": str(row["user_id"]) if row.get("user_id") else None,
        "displayName": row["display_name"],
        "body": row["body"],
        "isBot": bool(row.get("is_bot", False)),
        "kind": row.get("kind") or "text",
        "meta": row.get("meta") or {},
        "createdAt": row.get("created_at") or _now(),
    }


def _assemble(room: dict, members: list[dict], messages: list[dict]) -> dict:
    return {
        "id": room["id"],
        "code": room["code"],
        "name": room["name"],
        "tripId": room.get("trip_id"),
        "generatedTripId": room.get("generated_trip_id"),
        "hostUserId": str(room["host_user_id"]),
        "tripBrief": room.get("trip_brief") or {},
        "generatedTripBrief": room.get("generated_trip_brief") or {},
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
        "messages": [_message_dict(row) for row in messages],
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


def list_rooms_for_user(user_id: str, *, page: int = 1, page_size: int = 20) -> dict:
    """Paginated, batch-fetched list of rooms a user belongs to.

    Replaces the previous per-membership loop (one collab_rooms query, plus a
    members query and a messages query per room) with one `.in_()` query per
    related table, no matter how many rooms the user is in.
    """
    sb = get_supabase()
    memberships = sb.table("collab_members").select("room_id").eq("user_id", user_id).execute()
    room_ids = list(dict.fromkeys(row["room_id"] for row in memberships.data or []))
    if not room_ids:
        return {"items": [], "page": page, "pageSize": page_size, "hasMore": False}

    room_rows = (sb.table("collab_rooms").select("*").in_("id", room_ids).execute()).data or []
    all_members = (sb.table("collab_members").select("*").in_("room_id", room_ids).execute()).data or []
    all_messages = (
        sb.table("collab_messages").select("*").in_("room_id", room_ids).order("created_at").execute()
    ).data or []

    members_by_room: dict[str, list[dict]] = {}
    for member in all_members:
        members_by_room.setdefault(member["room_id"], []).append(member)
    messages_by_room: dict[str, list[dict]] = {}
    for message in all_messages:
        messages_by_room.setdefault(message["room_id"], []).append(message)

    rooms = [
        _assemble(room, members_by_room.get(room["id"], []), messages_by_room.get(room["id"], []))
        for room in room_rows
    ]
    rooms.sort(key=lambda item: item["createdAt"], reverse=True)

    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": rooms[start:end],
        "page": page,
        "pageSize": page_size,
        "hasMore": end < len(rooms),
    }


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
            "kind": "text",
        }
    ).execute()
    if not inserted.data:
        raise RuntimeError("Failed to post message")
    return _message_dict(inserted.data[0])


def add_bot_message(
    *,
    code: str,
    display_name: str,
    body: str,
    kind: str = "text",
    meta: dict | None = None,
) -> dict | None:
    room = get_room_by_code(code)
    if room is None:
        raise KeyError("room_not_found")
    inserted = get_supabase().table("collab_messages").insert(
        {
            "room_id": room["id"],
            "user_id": None,
            "display_name": display_name,
            "body": body,
            "is_bot": True,
            "kind": kind,
            "meta": meta or {},
        }
    ).execute()
    if not inserted.data:
        return None
    return _message_dict(inserted.data[0])


def add_system_message(*, code: str, display_name: str, body: str) -> dict | None:
    return add_bot_message(code=code, display_name=display_name, body=body, kind="system")


def get_message(message_id: str) -> dict | None:
    rows = get_supabase().table("collab_messages").select("*").eq("id", message_id).limit(1).execute()
    if not rows.data:
        return None
    return _message_dict(rows.data[0])


def set_message_resolved_meta(message_id: str, resolved: dict) -> None:
    message = get_message(message_id)
    if message is None:
        return
    meta = dict(message.get("meta") or {})
    meta["resolved"] = resolved
    get_supabase().table("collab_messages").update({"meta": meta}).eq("id", message_id).execute()


def resolve_field(
    *,
    code: str,
    field: str,
    value: str,
    option_label: str,
    set_by_user_id: str | None,
    set_by_name: str,
    allow_overwrite: bool = False,
) -> dict | None:
    """Sets one trip_brief field, by default first-write-wins unless `allow_overwrite=True`.

    Returns the resolution that ended up in place (which may belong to someone else
    if they beat this call), or None if the room doesn't exist. Any room member can
    update an already-set field later — callers pass `allow_overwrite=True` for that
    so the newest call wins rather than the first.

    Not perfectly atomic against a concurrent write between the read and this update —
    acceptable for a small group trip-planning chat; a lost race here just means
    whichever write lands last wins, which is fine for a live group chat.
    """
    room = get_room_by_code(code)
    if room is None:
        return None
    brief: dict = dict(room.get("tripBrief") or {})
    existing = brief.get(field)
    if existing and not allow_overwrite:
        return existing

    resolution = {
        "value": value,
        "optionLabel": option_label,
        "setByUserId": set_by_user_id,
        "setByName": set_by_name,
        "setAt": _now(),
    }
    brief[field] = resolution
    get_supabase().table("collab_rooms").update({"trip_brief": brief}).eq("id", room["id"]).execute()
    return resolution


def set_generated_trip(code: str, trip_id: str, trip_brief_snapshot: dict) -> None:
    get_supabase().table("collab_rooms").update(
        {"generated_trip_id": trip_id, "generated_trip_brief": trip_brief_snapshot}
    ).eq("code", code.upper()).execute()
