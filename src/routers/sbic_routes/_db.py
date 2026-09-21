"""Shared SBIC DB engine and query helper."""
from typing import Any, Optional
from fastapi import HTTPException, status
from sqlalchemy import text
from src.db.dbconn import DbConn
from src.logger import logger

_sbic_engine = None


def get_sbic_engine():
    global _sbic_engine
    if _sbic_engine is None:
        _sbic_engine = DbConn(logger, 'sbic').main()
    return _sbic_engine


def _invalidate_engine():
    """Drop the cached engine so the next request creates a fresh one."""
    global _sbic_engine
    _sbic_engine = None


def run_query(query: str, params: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Execute a read query against sbic_prod and return rows as dicts.

    Converts DB access failures into HTTPExceptions consistently across all
    sbic_routes endpoints, and drops the cached engine on login failures so
    the next request retries with a fresh connection.
    """
    try:
        engine = get_sbic_engine()
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        err = str(e)
        if "Login failed" in err or "Cannot open database" in err:
            _invalidate_engine()
            logger.error(f"[sbic] access denied: {e}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied connecting to sbic_prod. Check MSSQL credentials/permissions.",
            )
        logger.error(f"[sbic] query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err)
