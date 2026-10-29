"""General endpoint for the SBIC handoff process."""

import base64, json, logging, time
from google.api_core.exceptions import AlreadyExists
from google.cloud import logging as cloud_logging
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from fastapi import HTTPException, Query, Request, status, APIRouter, Depends
from src.config import pass_key
import src.config as config
from src.routers.sbic_routes.rate_limiter import rate_limit
from src.services.bridge_trigger import publish_bridge_run

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('handoff')

handoff_router = APIRouter(prefix="/handoff", tags=["SBICHandoff"])


def _extract_bq_destination_table(body) -> str | None:
    """Best-effort extraction of the destination table resource path
    (projects/.../datasets/.../tables/...) from a BigQuery JobService.InsertJob Cloud
    Audit Log event, however it arrives on delivery (Pub/Sub-push-wrapped, CloudEvents
    structured-mode, or the raw LogEntry body). Returns None on anything unrecognized
    -- NEVER raises, and callers must treat None as "can't tell, so don't filter it
    out" rather than as "unrelated"."""
    try:
        if isinstance(body, dict) and isinstance(body.get("message"), dict) and "data" in body["message"]:
            # Pub/Sub push subscription wrapping: {"message": {"data": "<base64>", ...}}
            body = json.loads(base64.b64decode(body["message"]["data"]).decode("utf-8"))
        if isinstance(body, dict) and "protoPayload" not in body and isinstance(body.get("data"), dict):
            # CloudEvents structured-mode envelope: {"data": {...LogEntry...}, ...}
            body = body["data"]
        job_config = body["protoPayload"]["metadata"]["jobInsertion"]["job"]["jobConfig"]
        for key in ("queryConfig", "loadConfig", "copyConfig", "extractConfig"):
            dest = (job_config.get(key) or {}).get("destinationTable")
            if dest:
                return dest
    except Exception:
        pass
    return None

@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    method: str = 'manual',
    groupcode: str = Query(None, description="Group code override for manual calls"),
    _: None = Depends(rate_limit)
):
    """Publishes a bridge-run request instead of running BigqueryBridge.main() inline
    -- see src/services/bridge_trigger.py for why. rate_limit stays here as cheap
    defense-in-depth against a misbehaving trigger spamming publishes; the real
    mutual exclusion now lives in rgmc-worker-pool's FlowControl(max_messages=1)."""
    if groupcode is None:
        groupcode = 'customerpoul'
    return publish_bridge_run(groupcode, method)


@handoff_router.post("/runbridge/debounce/")
async def run_handoff_bridge_debounced(
    request: Request,
    method: str = 'triggered',
    groupcode: str = Query(None, description="Group code override"),
):
    """Eventarc-facing endpoint: instead of calling the bridge directly (several
    Eventarc triggers can fire within the same second for one upload batch -- a
    single Document AI batch output or BigQuery insert burst), schedule ONE
    delayed Cloud Task per (group_code, time bucket) that calls the real
    /handoff/runbridge/ ~runbridge_debounce_seconds later. Cloud Tasks rejects a
    second task created with the same name, so every extra event in the same
    burst just gets an "already_scheduled" no-op here instead of its own bridge
    run -- collapsing N concurrent invocations into 1.

    groupcode="customerra" is also wired as the destination of
    bq-int-document-ai-ra-trigger-v2, a Cloud Audit Log Eventarc trigger matching
    serviceName=bigquery.googleapis.com + methodName=JobService.InsertJob with NO
    table-specific scoping -- Eventarc's audit-log filters can't match a field this
    deep in the payload. Confirmed live (2026-10-29) that this fires on EVERY
    BigQuery job in the whole project, including scheduled dbt builds of models with
    no connection to int_document_ai_ra at all (e.g. an inventory view), not just real
    RA data arriving -- flooding the logs and calling the Cloud Tasks API for
    something there's nothing to debounce. Filtered out here (after delivery, since
    this is the only place precise enough to check it) whenever the event's own
    destination table can be positively identified as something else; any event whose
    destination table can't be determined is still treated as relevant (fails open),
    so an unrecognized payload shape never silently drops a genuine RA trigger.
    """
    if groupcode is None:
        groupcode = 'customerpoul'

    if groupcode == "customerra":
        try:
            body = await request.json()
        except Exception:
            body = None
        dest_table = _extract_bq_destination_table(body) if body else None
        if dest_table is not None and not dest_table.endswith(f"/datasets/{config.bigquery_dataset_id}/tables/int_document_ai_ra"):
            logger.debug(f"[handoff] debounce: ignoring unrelated BigQuery job (destination={dest_table!r})")
            return {"status": "ignored", "group_code": groupcode, "reason": "unrelated BigQuery destination table", "destination_table": dest_table}

    bucket_start = int(time.time() // config.runbridge_debounce_seconds) * config.runbridge_debounce_seconds
    fire_at = bucket_start + config.runbridge_debounce_seconds
    task_id = f"{groupcode}-{bucket_start}"

    tasks_client = tasks_v2.CloudTasksClient()
    queue_path = tasks_client.queue_path(
        config.cloud_tasks_project_id, config.cloud_tasks_location, config.cloud_tasks_queue
    )
    task_path = tasks_client.task_path(
        config.cloud_tasks_project_id, config.cloud_tasks_location, config.cloud_tasks_queue, task_id
    )

    schedule_time = timestamp_pb2.Timestamp()
    schedule_time.FromSeconds(fire_at)

    task = {
        "name": task_path,
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{config.runbridge_service_url}/handoff/runbridge/?method={method}&groupcode={groupcode}",
            "oidc_token": {"service_account_email": config.runbridge_invoker_service_account},
        },
        "schedule_time": schedule_time,
    }

    try:
        tasks_client.create_task(request={"parent": queue_path, "task": task})
        logger.info(f"[handoff] debounce: scheduled '{task_id}' to fire at {fire_at} (epoch)")
        return {"status": "scheduled", "group_code": groupcode, "task_id": task_id, "fire_at_epoch": fire_at}
    except AlreadyExists:
        # DEBUG, not INFO -- this is the expected, harmless outcome for every event in
        # a burst after the first one (that's the whole point of debouncing), and
        # customerra's over-broad trigger (see this function's docstring) could fire
        # dozens of these for one unrelated dbt run alone.
        logger.debug(f"[handoff] debounce: '{task_id}' already scheduled by an earlier event in this burst")
        return {"status": "already_scheduled", "group_code": groupcode, "task_id": task_id, "fire_at_epoch": fire_at}
    except Exception as e:
        logger.error(f"[handoff] debounce: error scheduling task '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
