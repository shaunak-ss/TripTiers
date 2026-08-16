from __future__ import annotations

import json
from typing import Any

from anthropic import APIConnectionError, APIStatusError, AsyncAnthropic, AuthenticationError, PermissionDeniedError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import tool_json_schema

log = get_logger(__name__)

_client: AsyncAnthropic | None = None


def _coerce_stringified_json(value: Any) -> Any:
    """Claude's forced tool_use occasionally emits a nested array/object field as a
    JSON-encoded string instead of native JSON. Recursively unwrap those before validation.
    Occasionally it also glues trailing content (e.g. a sibling field it meant to emit
    separately) onto the end of that string — raw_decode parses just the leading valid
    JSON value and ignores whatever comes after, instead of failing on the whole string."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in "[{":
            try:
                parsed, _end = json.JSONDecoder().raw_decode(stripped)
                return _coerce_stringified_json(parsed)
            except json.JSONDecodeError:
                return value
        return value
    if isinstance(value, list):
        return [_coerce_stringified_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _coerce_stringified_json(item) for key, item in value.items()}
    return value


def get_anthropic() -> AsyncAnthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, max=4),
    retry=retry_if_exception_type((APIStatusError, APIConnectionError, TimeoutError)),
    reraise=True,
)
async def create_structured_output(
    *,
    system: str,
    user: str,
    schema: type[BaseModel],
    tool_name: str,
    timeout_s: float,
    extra_cached_blocks: list[dict[str, Any]] | None = None,
) -> Any:
    """
    Claude structured output via forced tool_use.
    `system` MUST be a list of content blocks so cache_control can attach —
    a plain-string system= silently disables prompt caching.
    """
    settings = get_settings()
    input_schema = tool_json_schema(schema)
    system_blocks: list[dict[str, Any]] = [
        {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}},
        *(extra_cached_blocks or []),
    ]

    try:
        response = await get_anthropic().messages.create(
            model=settings.anthropic_model,
            max_tokens=8192,
            system=system_blocks,
            tools=[
                {
                    "name": tool_name,
                    "description": "Emit the structured result. You MUST call this tool with a complete payload.",
                    "input_schema": input_schema,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tool_choice={"type": "tool", "name": tool_name},
            messages=[{"role": "user", "content": user}],
            timeout=timeout_s,
        )
    except (AuthenticationError, PermissionDeniedError) as exc:
        raise AppError(
            502,
            "claude_auth_failed",
            "Claude API rejected the request — ANTHROPIC_API_KEY in backend/.env is missing, invalid, or lacks access. Get a real key from console.anthropic.com.",
        ) from exc

    usage = getattr(response, "usage", None)
    if usage:
        log.info(
            "claude usage",
            tool=tool_name,
            cache_read=getattr(usage, "cache_read_input_tokens", None),
            cache_write=getattr(usage, "cache_creation_input_tokens", None),
        )

    tool_block = next((b for b in response.content if getattr(b, "type", None) == "tool_use"), None)
    if tool_block is None:
        raise RuntimeError("Claude did not return structured output")

    raw = tool_block.input
    log.info("claude structured output", tool=tool_name, raw=raw)
    return schema.model_validate(_coerce_stringified_json(raw))
