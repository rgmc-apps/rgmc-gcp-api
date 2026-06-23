"""Generic SQL Server database direct-read endpoints (all db_mappings databases)."""
import logging
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from src.db.dbconn import DbConn
from src.logger import logger as app_logger
import src.mappings as mappings

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("sbic_routes")

sbic_router = APIRouter(tags=["SBIC"])

_engines = {}


def _get_engine(db_name: str):
    if db_name not in _engines:
        _engines[db_name] = DbConn(app_logger, db_name).main()
    return _engines[db_name]


def _validate_db(db_name: str):
    if db_name not in mappings.db_mappings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{db_name}' not found. Valid options: {list(mappings.db_mappings.keys())}",
        )


@sbic_router.get("/{db_name}/by_table/value")
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
        logger.error(f"[{db_name}] query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sbic_router.get("/{db_name}/by_table/latest")
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
        logger.error(f"[{db_name}] query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
