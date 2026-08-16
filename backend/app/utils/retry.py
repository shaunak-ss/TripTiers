"""Project-wide retry: max 2 attempts, exponential backoff, always time-bounded."""

from collections.abc import Callable
from typing import TypeVar

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

T = TypeVar("T")


def default_retry(fn: Callable[..., T]) -> Callable[..., T]:
    return retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=0.5, max=4),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError)),
        reraise=True,
    )(fn)
