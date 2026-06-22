"""SBIC direct-read endpoints."""
import logging
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from src.routers.sbic_routes._db import get_sbic_engine

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("sbic_routes")

sbic_router = APIRouter(prefix="/sbic", tags=["SBIC"])


@sbic_router.get("/by_table/value")
async def get_by_value(
    table_name: str = Query(...),
    where_column: str = Query(...),
    where_value: str = Query(...),
):
    try:
        engine = get_sbic_engine()
        query = "SELECT * FROM {} WHERE {} = :where_value".format(table_name, where_column)
        with engine.connect() as conn:
            result = conn.execute(text(query), {"where_value": where_value})
            rows = [dict(row._mapping) for row in result]
        return {"record_count": len(rows), "data": rows}
    except Exception as e:
        logger.error(f"SBIC query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sbic_router.get("/by_table/latest")
async def get_latest(
    table_name: str = Query(...),
    date_column: str = Query(...),
    number_of_rows: int = Query(100, ge=1, le=10000),
):
    try:
        engine = get_sbic_engine()
        query = "SELECT TOP {} * FROM {} ORDER BY {} DESC".format(number_of_rows, table_name, date_column)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = [dict(row._mapping) for row in result]
        return {"record_count": len(rows), "data": rows}
    except Exception as e:
        logger.error(f"SBIC query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
