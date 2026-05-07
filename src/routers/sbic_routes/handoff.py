"""General endpoint for the SBIC handoff process."""

import base64, json, logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, APIRouter, Depends
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('handoff')

handoff_router = APIRouter(prefix="/handoff", tags=["SBICHandoff"])

@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    method: str = 'manual',
    groupcode: str = Query(None, description="Optional group code to determine which BigQuery bridge to run. If not provided, it will be inferred from the payload.")
):
    try:
        if groupcode is None:
            groupcode = 'customerpoul'  # Default group code if not provided
        bridge = BigqueryBridge(logger, method, group_code=groupcode)
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"[handoff] error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
