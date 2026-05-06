"""General endpoint for the SBIC handoff process."""

import base64, json, logging
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
    """Pull the BQ table name from an Eventarc Cloud Audit Log CloudEvent payload.

    Handles three delivery shapes Eventarc may use:
      1. Structured mode  — body is full CloudEvent; audit log is under payload['data']
      2. Binary mode      — body IS the LogEntry directly; protoPayload at top level
      3. Base64 data      — payload['data'] is a base64 string wrapping the LogEntry
    """
    # Shape 1 & 3: CloudEvent envelope with 'data' field
    data = payload.get('data')
    if isinstance(data, str):
        # base64-encoded LogEntry — decode first
        try:
            data = json.loads(base64.b64decode(data).decode('utf-8'))
        except Exception:
            data = {}
    if isinstance(data, dict):
        resource_name = data.get('protoPayload', {}).get('resourceName', '')
        if resource_name:
            return resource_name.split('/tables/')[-1] if '/tables/' in resource_name else ''

    # Shape 2: body is the LogEntry directly
    resource_name = payload.get('protoPayload', {}).get('resourceName', '')
    if resource_name:
        return resource_name.split('/tables/')[-1] if '/tables/' in resource_name else ''

    return ''


@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    request: Request,
    method: str = 'manual'
):
    try:
        group_code = 'customerpoul'  # default for manual calls

        if method == 'triggered':
            try:
                payload = await request.json()
                logger.info(f"[handoff] raw payload keys: {list(payload.keys())}")

                table_name = _extract_table_name(payload)
                logger.info(f"[handoff] extracted table_name='{table_name}'")

                mapped = _TABLE_GROUP_MAP.get(table_name)
                if not mapped:
                    logger.warning(f"[handoff] blocked: table '{table_name}' not in mapping")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"table '{table_name}' is not a recognised handoff target"
                    )
                group_code = mapped
                logger.info(f"[handoff] trigger matched table='{table_name}' → group_code='{group_code}'")
            except HTTPException:
                raise
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
