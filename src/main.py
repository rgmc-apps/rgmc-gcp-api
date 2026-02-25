import os
import time
import pandas_gbq
import src.config as config
import src.db.dbconn as dbconn
from fastapi import FastAPI, Request
from typing import Any, Callable
from src.logger import logger
from src.routers import healthrouter
from sqlalchemy import text

try:
    api = FastAPI(title=f"RGMC API", version=config.__version__)
    mssql_engine = dbconn.DbConn(logger, 'sbic').main()
    api.include_router(healthrouter)
except Exception as e:
    logger.error(f"Error initializing FastAPI: {e}")
    raise e

@api.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable) -> Any:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@api.get("/index")
def index():
    logger.info("Index endpoint called")
    return {"status": "Api is running"}

@api.get("/checkdb")
def check_db():
    try:
        with mssql_engine.connect() as connection:
            result = connection.execute(
                text("SELECT * from sbic_prod.dbo.Company")
            ).fetchall()
            logger.info("Database connection successful")
            return {"database_status": "connected", "result": [row[0] for row in result]}
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {"database_status": "error", "error": str(e)}

@api.get("/checkBigQuery")
def check_bigquery():
    try:
        query = "SELECT * FROM `{}.int_document_ai_detail`".format(config.bigquery_dataset_id)
                
        df = pandas_gbq.read_gbq(
            query,
            project_id=config.bigquery_project_id,
            dialect='standard'
        )
        logger.info(f"Fetched {len(df)} records from BigQuery.")

        return {"bigquery_status": "connected", "record_count": len(df), "returned_data": df.head(5).to_dict(orient='records')}
    except Exception as e:
        logger.error(f"BigQuery connection failed: {e}")
        return {"bigquery_status": "error", "error": str(e)}