"""CustomerPOUL Related Queries and Functions."""
import logging
from google.cloud import logging as cloud_logging
from fastapi import FastAPI, HTTPException, status, Depends, APIRouter
from bigquery_bridge import BigqueryBridge

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging() 

logger = logging.getLogger('customerpoul')

customerpoul_router = APIRouter(prefix="/customerpoul", tags=["CustomerPOUL"])

@customerpoul_router.post("/runbridge")
async def run_bigquery_bridge():
    try:
        bridge = BigqueryBridge(logger)
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
