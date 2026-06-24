"""CustomerPOUL Related Queries and Functions."""

import logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, Depends, APIRouter
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging() 

logger = logging.getLogger('customerpoul')

customerpoul_router = APIRouter(prefix="/customerpoul", tags=["CustomerPOUL"])

@customerpoul_router.post("/runbridge/")
async def run_customerpoul_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='customerpoul')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customerpoul_router.post("/runbridge/onlinesalespo/")
async def run_online_sales_po_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='onlinesalespo')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))