"""Customer Remittance Advice (RA)."""

import logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, Depends, APIRouter
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit
from src.services.bridge_trigger import publish_bridge_run

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('customer_ra')

customer_ra_router = APIRouter(prefix="/customerra", tags=["CustomerRA"])

@customer_ra_router.post("/runbridge/", dependencies=[Depends(rate_limit)])
async def run_remittance_advice_bridge(request: Request, method: str = 'manual'):
    """Publishes a bridge-run request instead of running BigqueryBridge.main() inline
    -- see rgmc-gcp-api's src/services/bridge_trigger.py and handoff.md ("Move
    bigquery_bridge heavy work to worker pool")."""
    return publish_bridge_run('customerra', method)
