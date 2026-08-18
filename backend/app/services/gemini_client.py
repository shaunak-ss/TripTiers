from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import errors, types
from pydantic import BaseModel
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.errors import AppError
from app.utils.logger import get_logger
from app.validators.schemas import tool_json_schema

log = get_logger(__name__)

_client: genai.Client | None = None


def _coerce_stringified_json(value: Any) -> Any:
    """Gemini structured output occasionally emits a nested array/object field as a
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


def _system_instruction(system: str, extra_cached_blocks: list[dict[str, Any]] | None) -> str:
    parts = [system]
    for block in extra_cached_blocks or []:
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def _parse_json_payload(text: str) -> Any:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
        fence = stripped.rfind("```")
        if fence != -1:
            stripped = stripped[:fence]
        stripped = stripped.strip()
    return json.loads(stripped)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, TimeoutError):
        return True
    if isinstance(exc, errors.ServerError):
        return True
    code = getattr(exc, "code", None)
    return isinstance(exc, errors.APIError) and code in {408, 429, 500, 502, 503, 504}


def get_gemini() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, max=4),
    retry=retry_if_exception(_is_retryable),
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
    """Gemini structured output via JSON response schema.

    Same call shape as the previous Claude tool_use client so agents stay unchanged.
    Extra grounding blocks (formerly Claude prompt-cache blocks) are appended to the
    system instruction.

    Deliberately omits `thinking_config` — across the current model lineup
    (gemini-flash-lite-latest, gemini-3.5-flash-lite, gemini-3.6-flash) setting
    `thinking_budget=0` returns a hard 400 INVALID_ARGUMENT instead of just
    being ignored, so it's not safe to send at all right now.
    """
    settings = get_settings()
    input_schema = tool_json_schema(schema)
    system_text = _system_instruction(system, extra_cached_blocks)

    try:
        response = await get_gemini().aio.models.generate_content(
            model=settings.gemini_model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system_text,
                response_mime_type="application/json",
                response_json_schema=input_schema,
                max_output_tokens=8192,
                temperature=0,
                http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),
            ),
        )
    except errors.ClientError as exc:
        message = (getattr(exc, "message", None) or str(exc)).lower()
        code = getattr(exc, "code", None)
        if code in (401, 403) or "api key" in message:
            raise AppError(
                502,
                "gemini_auth_failed",
                "Gemini API rejected the request — GEMINI_API_KEY in backend/.env is missing, invalid, or lacks access. Get a free key from aistudio.google.com/apikey.",
            ) from exc
        raise

    usage = getattr(response, "usage_metadata", None)
    if usage:
        log.info(
            "gemini usage",
            tool=tool_name,
            prompt_tokens=getattr(usage, "prompt_token_count", None),
            output_tokens=getattr(usage, "candidates_token_count", None),
        )

    raw_text = getattr(response, "text", None)
    if not raw_text:
        raise RuntimeError("Gemini did not return structured output")

    try:
        raw = _parse_json_payload(raw_text)
    except json.JSONDecodeError:
        coerced = _coerce_stringified_json(raw_text)
        if isinstance(coerced, str):
            raise RuntimeError("Gemini did not return structured output") from None
        raw = coerced

    log.info("gemini structured output", tool=tool_name, raw=raw)
    return schema.model_validate(_coerce_stringified_json(raw))
