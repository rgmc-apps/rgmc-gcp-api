"""Customer Remittance Advice (RA)."""

import logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, Depends, APIRouter
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging() 

logger = logging.getLogger('customer_ra')

customer_ra_router = APIRouter(prefix="/customerra", tags=["CustomerRA"])

@customer_ra_router.post("/runbridge/", dependencies=[Depends(rate_limit)])
async def run_remittance_advice_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='customerra')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
