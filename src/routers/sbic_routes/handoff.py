"""General endpoint for the SBIC handoff process."""

import logging
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, APIRouter
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('handoff')

handoff_router = APIRouter(prefix="/handoff", tags=["SBICHandoff"])

_TABLE_GROUP_MAP = {
    'int_document_ai':    'customerpoul',
    'int_document_ai_ra': 'customerra',
}


def _extract_table_name(payload: dict) -> str:
    """Pull the BQ table name from an Eventarc Cloud Audit Log CloudEvent payload."""
    resource_name = (
        payload.get('protoPayload', {}).get('resourceName')
        or payload.get('data', {}).get('protoPayload', {}).get('resourceName')
        or ''
    )
    if '/tables/' in resource_name:
        return resource_name.split('/tables/')[-1]
    return ''


@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    request: Request,
    method: str = 'manual',
):
    try:
        # if passkey != pass_key:
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid passkey")

        group_code = 'customerpoul'  # default for manual calls

        if method == 'triggered':
            try:
                payload = await request.json()
                table_name = _extract_table_name(payload)
                mapped = _TABLE_GROUP_MAP.get(table_name)
                if not mapped:
                    logger.warning(f"[handoff] blocked: table '{table_name}' not in mapping")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"table '{table_name}' is not a recognised handoff target"
                    )
                group_code = mapped
                logger.info(f"[handoff] trigger matched table='{table_name}' → group_code='{group_code}'")
            except Exception as e:
                logger.warning(f"[handoff] could not parse trigger payload: {e}")
                return {"detail": "skipped: could not parse payload"}

        bridge = BigqueryBridge(logger, method, group_code=group_code)
        result = bridge.main()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[handoff] error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
