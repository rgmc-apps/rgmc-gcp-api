"""BigQuery direct-read endpoints."""
import logging
import pandas_gbq
import src.config as config
from fastapi import APIRouter, HTTPException, Query, status
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger("bigquery_routes")

bigquery_router = APIRouter(prefix="/bigquery_routes", tags=["BigQuery"])


@bigquery_router.get("/by_table/value")
async def get_by_value(
    table_name: str = Query(...),
    where_column: str = Query(...),
    where_value: str = Query(...),
):
    try:
        query = "SELECT * FROM `{}.{}` WHERE {} = '{}'".format(
            config.bigquery_dataset_id, table_name, where_column, where_value
        )
        df = pandas_gbq.read_gbq(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bigquery_router.get("/by_table/latest")
async def get_latest(
    table_name: str = Query(...),
    date_column: str = Query(...),
):
    try:
        query = "SELECT * FROM `{}.{}` ORDER BY {} DESC LIMIT 100".format(
            config.bigquery_dataset_id, table_name, date_column
        )
        df = pandas_gbq.read_gbq(query, project_id=config.bigquery_project_id, dialect="standard")
        return {"record_count": len(df), "data": df.to_dict(orient="records")}
    except Exception as e:
        logger.error(f"BigQuery query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
