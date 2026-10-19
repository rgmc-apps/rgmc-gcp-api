"""Generic SQL Server database direct-read endpoints (all db_mappings databases)."""
import asyncio
import base64
import logging
import os
import threading
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from src.db.dbconn import DbConn
from src.logger import logger as app_logger
import src.mappings as mappings

# These routes are declared `async def` but pytds (the MSSQL DBAPI driver) has no
# asyncio support -- calling engine.connect()/.execute() directly here would block this
# service's single event loop (uvicorn runs with no --workers override) for the full
# query duration, freezing EVERY request this instance is handling, not just this one.
# Confirmed live (2026-10-19): a dashboard MSSQL status check took 34s, and an unrelated
# BigQuery lookup on the same instance stalled for 33-35s at the same time, with latency
# climbing across the sequence as requests queued up behind the blocked loop. Routing the
# query through asyncio.to_thread lets the event loop keep serving other requests while
# it runs, and the timeout turns a slow/stuck query into a fast, diagnosable 504 instead
# of the caller eventually hitting a generic client-side read timeout.
MSSQL_READ_TIMEOUT_SECONDS = float(os.getenv("MSSQL_READ_TIMEOUT_SECONDS", "20"))


def _serialize_value(value):
    """JSON can't carry raw bytes — base64-encode binary column values (e.g. varbinary/image)."""
    if isinstance(value, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(value)).decode("ascii")
    return value


def _serialize_row(row_mapping) -> dict:
    return {key: _serialize_value(value) for key, value in dict(row_mapping).items()}

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("mssql_routes")

mssql_router = APIRouter(tags=["MSSQL"])

_engines = {}
_engines_lock = threading.Lock()


def _get_engine(db_name: str):
    # asyncio.to_thread (see _run_query) means this can now be called from multiple
    # worker threads at once -- lock the check-then-create so two concurrent first
    # requests for the same db_name can't each build and orphan their own engine.
    if db_name not in _engines:
        with _engines_lock:
            if db_name not in _engines:
                _engines[db_name] = DbConn(app_logger, db_name).main()
    return _engines[db_name]


def _invalidate_engine(db_name: str):
    """Remove a cached engine so the next request creates a fresh one."""
    _engines.pop(db_name, None)


def _validate_db(db_name: str):
    if db_name not in mappings.db_mappings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{db_name}' not found. Valid options: {list(mappings.db_mappings.keys())}",
        )


def _handle_db_error(db_name: str, e: Exception) -> HTTPException:
    """Convert a low-level DB exception to a descriptive HTTPException."""
    err = str(e)
    physical_db = mappings.db_mappings.get(db_name, db_name)

    # SQL Server login / access denied — surface as 403 so callers can distinguish
    # permission problems from query errors
    if "Login failed" in err or "Cannot open database" in err:
        _invalidate_engine(db_name)   # don't cache a broken engine
        logger.error(f"[{db_name}] access denied to '{physical_db}': {e}")
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied: the SQL login does not have permission to open "
                f"'{physical_db}'. Ask a DBA to run: "
                f"USE [{physical_db}]; CREATE USER [<login>] FOR LOGIN [<login>]; "
                f"ALTER ROLE [db_datareader] ADD MEMBER [<login>];"
            ),
        )

    logger.error(f"[{db_name}] query error: {e}")
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=err)


async def _run_query(db_name: str, query: str, params: dict = None):
    """Runs the blocking SQLAlchemy/pytds call in a worker thread (see module docstring
    comment above) bounded by MSSQL_READ_TIMEOUT_SECONDS."""

    def _execute():
        engine = _get_engine(db_name)
        with engine.connect() as conn:
            result = conn.execute(text(query), params or {})
            return [_serialize_row(row._mapping) for row in result]

    try:
        return await asyncio.wait_for(asyncio.to_thread(_execute), timeout=MSSQL_READ_TIMEOUT_SECONDS)
    except asyncio.TimeoutError:
        raise TimeoutError(f"MSSQL read timed out after {MSSQL_READ_TIMEOUT_SECONDS:.0f}s") from None


@mssql_router.get("/{db_name}/by_table/value")
async def get_by_value(
    db_name: str,
    table_name: str = Query(...),
    where_column: str = Query(...),
    where_value: str = Query(...),
):
    _validate_db(db_name)
    query = "SELECT * FROM {} WHERE {} = :where_value".format(table_name, where_column)
    try:
        rows = await _run_query(db_name, query, {"where_value": where_value})
        return {"record_count": len(rows), "data": rows}
    except TimeoutError as e:
        logger.error(f"[{db_name}] by_table/value timed out (table={table_name}): {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_db_error(db_name, e)


@mssql_router.get("/{db_name}/by_table/latest")
async def get_latest(
    db_name: str,
    table_name: str = Query(...),
    date_column: str = Query(...),
    number_of_rows: int = Query(100, ge=1, le=10000),
):
    _validate_db(db_name)
    query = "SELECT TOP {} * FROM {} ORDER BY {} DESC".format(number_of_rows, table_name, date_column)
    try:
        rows = await _run_query(db_name, query)
        return {"record_count": len(rows), "data": rows}
    except TimeoutError as e:
        logger.error(f"[{db_name}] by_table/latest timed out (table={table_name}): {e}")
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_db_error(db_name, e)
