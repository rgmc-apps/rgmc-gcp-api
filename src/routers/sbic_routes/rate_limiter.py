"""Per-endpoint rate limiter: one call per 30s cooldown, per route path + groupcode."""

import time
from fastapi import HTTPException, Request, status

_last_called: dict[str, float] = {}
COOLDOWN_SECONDS = 30


def rate_limit(request: Request) -> None:
    # Keyed on path + groupcode -- /handoff/runbridge/ serves multiple independent
    # pipelines (customerpoul, customerra, ...) behind the same path. Keying on path
    # alone meant a burst of one groupcode's calls (confirmed live: customerra, driven
    # by the over-broad bq-int-document-ai-ra-trigger-v2 audit-log trigger firing on
    # every BigQuery job in the project) could 429 an unrelated groupcode's call for
    # the full 30s cooldown, with no connection to that groupcode's own traffic at all.
    # Confirmed this starved a customerpoul upload for ~15.5 hours on 2026-10-05,
    # contributing to a 3-day delay before it reached MSSQL/BC -- and confirmed still
    # happening as of 2026-10-19. Defaults to 'customerpoul' to match
    # /handoff/runbridge/'s own default, so an explicit ?groupcode=customerpoul call
    # and a bare call land in the same bucket.
    groupcode = request.query_params.get("groupcode") or "customerpoul"
    key = f"{request.url.path}::{groupcode}"
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
