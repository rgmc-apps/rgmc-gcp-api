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


def _table_from_resource_name(resource_name: str) -> str:
    """Extract table ID from a resourceName that contains /tables/TABLE."""
    if '/tables/' in resource_name:
        return resource_name.split('/tables/')[-1]
    return ''


def _table_from_service_data(proto: dict) -> str:
    """For JobService.InsertJob the destination table is inside serviceData, not resourceName."""
    sd = proto.get('serviceData', {})
    # jobInsertion (job creation event)
    job = (
        sd.get('jobInsertResponse', {}).get('resource', {})
        or sd.get('jobCompletedEvent', {}).get('job', {})
    )
    cfg = job.get('jobConfiguration', {})
    dest = (
        cfg.get('query', {}).get('destinationTable', {})
        or cfg.get('load', {}).get('destinationTable', {})
    )
    return dest.get('tableId', '')


def _extract_table_name(payload: dict) -> tuple[str, str]:
    """Return (table_name, source_path) from an Eventarc Cloud Audit Log payload.

    Tries every known delivery shape:
      1. Structured CloudEvent  — audit log under payload['data']
      2. Base64 CloudEvent      — payload['data'] is a base64-encoded LogEntry
      3. Binary / direct        — LogEntry at top level (protoPayload at root)
    For JobService.InsertJob the table is inside serviceData, not resourceName.
    """
    # resolve the LogEntry dict regardless of delivery shape
    log_entry = None

    data = payload.get('data')
    if isinstance(data, str):
        try:
            data = json.loads(base64.b64decode(data).decode('utf-8'))
        except Exception:
            data = {}
    if isinstance(data, dict) and 'protoPayload' in data:
        log_entry = data                          # Shape 1 or 2
    elif 'protoPayload' in payload:
        log_entry = payload                       # Shape 3

    if not log_entry:
        return '', 'no_log_entry'

    proto = log_entry.get('protoPayload', {})
    if not isinstance(proto, dict):
        return '', 'protoPayload_not_dict'

    # Try resourceName first (works for TableDataService.InsertAll)
    table = _table_from_resource_name(proto.get('resourceName', ''))
    if table:
        return table, 'resourceName'

    # Fallback: dig into serviceData (works for JobService.InsertJob)
    table = _table_from_service_data(proto)
    if table:
        return table, 'serviceData'

    return '', 'not_found'


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

                table_name, source = _extract_table_name(payload)
                logger.info(f"[handoff] extracted table_name='{table_name}' via '{source}'")

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
