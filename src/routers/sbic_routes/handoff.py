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

_TABLE_GROUP_MAP = {
    'int_document_ai':    'customerpoul',
    'int_document_ai_ra': 'customerra',
}


def _resolve_group_code(payload: dict) -> str | None:
    """Extract BQ table name from Eventarc payload and map to group code.
    Returns None if the table is not in the mapping.
    Handles all Eventarc delivery shapes (structured, base64, binary/direct).
    """
    log_entry = None
    data = payload.get('data')
    if isinstance(data, str):
        try:
            data = json.loads(base64.b64decode(data).decode('utf-8'))
        except Exception:
            data = {}
    if isinstance(data, dict) and 'protoPayload' in data:
        log_entry = data
    elif 'protoPayload' in payload:
        log_entry = payload

    if not log_entry:
        return None

    proto = log_entry.get('protoPayload', {})
    if not isinstance(proto, dict):
        return None

    # Shape A: resourceName contains /tables/TABLE (streaming inserts)
    resource_name = proto.get('resourceName', '')
    if '/tables/' in resource_name:
        table = resource_name.split('/tables/')[-1]
        return _TABLE_GROUP_MAP.get(table)

    # Shape B: destination table inside serviceData (job-based inserts)
    sd = proto.get('serviceData', {})
    job = (
        sd.get('jobInsertResponse', {}).get('resource', {})
        or sd.get('jobCompletedEvent', {}).get('job', {})
    )
    cfg = job.get('jobConfiguration', {})
    dest = (
        cfg.get('query', {}).get('destinationTable', {})
        or cfg.get('load', {}).get('destinationTable', {})
    )
    table = dest.get('tableId', '')
    return _TABLE_GROUP_MAP.get(table) if table else None


@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    request: Request,
    method: str = 'manual',
    groupcode: str = Query(None, description="Group code override for manual calls")
):
    try:
        if method == 'triggered':
            try:
                payload = await request.json()
                resolved = _resolve_group_code(payload)
                if not resolved:
                    # Always return 200 for unrecognised tables — prevents Pub/Sub retries
                    logger.info(f"[handoff] skipped: table not in mapping. payload keys={list(payload.keys())}")
                    return {"detail": "skipped: table not in mapping"}
                groupcode = resolved
                logger.info(f"[handoff] trigger resolved group_code='{groupcode}'")
            except HTTPException:
                raise
            except Exception as e:
                # Return 200 so Pub/Sub does not retry unparseable payloads
                logger.warning(f"[handoff] skipped: could not parse payload: {e}")
                return {"detail": "skipped: could not parse payload"}

        if groupcode is None:
            groupcode = 'customerpoul'

        bridge = BigqueryBridge(logger, method, group_code=groupcode)
        result = bridge.main()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[handoff] error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
