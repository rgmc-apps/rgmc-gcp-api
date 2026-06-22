"""Per-endpoint rate limiter: one call per minute per route path."""

import time
from fastapi import HTTPException, Request, status

_last_called: dict[str, float] = {}
COOLDOWN_SECONDS = 30


def rate_limit(request: Request) -> None:
    key = request.url.path
    now = time.monotonic()
    last = _last_called.get(key)
    if last is not None:
        elapsed = now - last
        if elapsed < COOLDOWN_SECONDS:
            retry_after = int(COOLDOWN_SECONDS - elapsed) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Endpoint called too recently. Retry after {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )
    _last_called[key] = now
