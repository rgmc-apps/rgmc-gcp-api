import os
import time
import pandas_gbq
import src.config as config
import src.db.dbconn as dbconn
from fastapi import FastAPI, Request
from typing import Any, Callable
from src.logger import logger
from src.routers import healthrouter, customerpoul_router, customer_ra_router, tradeportal_router, handoff_router, bc_router, sales_order_router, item_router, customer_router, sales_credit_memo_router, retail_customer_router, sales_return_order_router, rgmc_contact_router
from sqlalchemy import text

tags_metadata = [
    {
        "name": "CustomerPOUL",
        "description": "SBIC Purchasing Order Upload (POUL) related queries and functions.",
        "externalDocs": {
            "description": "SBIC PO Uploader",
            "url": "https://po-uploader-935246372408.us-central1.run.app/",
        },
    },
    {
        "name": "CustomerRA",
        "description": "SBIC Customer Remittance Advice related queries and functions.",
        "externalDocs": {
            "description": "SBIC Customer RA Uploader",
            "url": "https://ra-uploader-935246372408.us-central1.run.app/",
        },
    },
    {
        "name": "Trade Portal",
        "description": "Trade Portal database read endpoints — brands, categories, colors, companies, customers, locations, products, SKUs, packing lists, pull outs, markdowns, and system tables.",
    },
    {
        "name": "SBICHandoff",
        "description": "SBIC Handoff related queries and functions.",
    },
    {
        "name": "Business Central",
        "description": "Business Central data endpoints — brands (dimension values), contacts, and customers.",
    },
    {
        "name": "BC Sales Orders",
        "description": "Business Central Sales Order CRUD endpoints.",
    },
    {
        "name": "BC Items",
        "description": "Business Central Item CRUD endpoints.",
    },
    {
        "name": "BC Customers",
        "description": "Business Central Customer CRUD endpoints.",
    },
    {
        "name": "BC Sales Credit Memos",
        "description": "Business Central Sales Credit Memo CRUD endpoints (sales return equivalent).",
    },
    {
        "name": "BC RGMC Retail Customers",
        "description": "RGMC custom API — Retail Customer CRUD endpoints (Pag50200, api/rgmc/rgmccustom/v1.0).",
    },
    {
        "name": "BC RGMC Sales Return Orders",
        "description": "RGMC custom API — Sales Return Order and Lines CRUD endpoints (Pag50201/Pag50202, api/rgmc/rgmccustom/v1.0).",
    },
    {
        "name": "BC RGMC Contacts",
        "description": "RGMC custom API — Contact CRUD endpoints (Pag50203, api/rgmc/rgmccustom/v1.0).",
    },
]

try:
    revision = config.revision_code
    api = FastAPI(title=f"RGMC API :  (Release - {revision})", docs_url="/swagger", version=config.__version__, openapi_tags=tags_metadata)
    mssql_engine = dbconn.DbConn(logger, 'sbic').main()
    api.include_router(healthrouter)
    api.include_router(customerpoul_router)
    api.include_router(customer_ra_router)
    api.include_router(tradeportal_router)
    api.include_router(handoff_router)
    api.include_router(bc_router)
    api.include_router(sales_order_router)
    api.include_router(item_router)
    api.include_router(customer_router)
    api.include_router(sales_credit_memo_router)
    api.include_router(retail_customer_router)
    api.include_router(sales_return_order_router)
    api.include_router(rgmc_contact_router)
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
        query = "SELECT * FROM `{}.int_document_ai_detail` LIMIT 10".format(config.bigquery_dataset_id)
                
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