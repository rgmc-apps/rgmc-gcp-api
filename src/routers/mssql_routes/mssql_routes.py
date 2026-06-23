"""Generic SQL Server database direct-read endpoints (all db_mappings databases)."""
import logging
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from src.db.dbconn import DbConn
from src.logger import logger as app_logger
import src.mappings as mappings

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("mssql_routes")

mssql_router = APIRouter(tags=["MSSQL"])

_engines = {}


def _get_engine(db_name: str):
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


@mssql_router.get("/{db_name}/by_table/value")
async def get_by_value(
    db_name: str,
    table_name: str = Query(...),
    where_column: str = Query(...),
    where_value: str = Query(...),
):
    _validate_db(db_name)
    try:
        engine = _get_engine(db_name)
        query = "SELECT * FROM {} WHERE {} = :where_value".format(table_name, where_column)
        with engine.connect() as conn:
            result = conn.execute(text(query), {"where_value": where_value})
            rows = [dict(row._mapping) for row in result]
        return {"record_count": len(rows), "data": rows}
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
    try:
        engine = _get_engine(db_name)
        query = "SELECT TOP {} * FROM {} ORDER BY {} DESC".format(number_of_rows, table_name, date_column)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
        return {"record_count": len(rows), "data": rows}
    except HTTPException:
        raise
    except Exception as e:
        raise _handle_db_error(db_name, e)
