"""Customer Remittance Advice (RA)."""

import logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, status, Depends, APIRouter
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging() 

logger = logging.getLogger('customer_ra')

customer_ra_router = APIRouter(prefix="/customerra", tags=["CustomerRA"])

@customer_ra_router.post("/runbridge/")
async def run_remittance_advice_bridge(method: str = 'manual', passkey: str = Query(..., description="Passkey for authentication")):
    try:
        if passkey != pass_key:  # Replace with actual passkey validation logic
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid passkey")
        bridge = BigqueryBridge(logger, method, group_code='customerra')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
