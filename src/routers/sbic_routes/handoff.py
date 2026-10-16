"""General endpoint for the SBIC handoff process."""

import base64, json, logging, time
from google.api_core.exceptions import AlreadyExists
from google.cloud import logging as cloud_logging
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from fastapi import HTTPException, Query, Request, status, APIRouter, Depends
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
import src.config as config
from src.routers.sbic_routes.rate_limiter import rate_limit

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('handoff')

handoff_router = APIRouter(prefix="/handoff", tags=["SBICHandoff"])

@handoff_router.post("/runbridge/")
async def run_handoff_bridge(
    method: str = 'manual',
    groupcode: str = Query(None, description="Group code override for manual calls"),
    _: None = Depends(rate_limit)
):
    try:
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


@handoff_router.post("/runbridge/debounce/")
async def run_handoff_bridge_debounced(
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
    """
    if groupcode is None:
        groupcode = 'customerpoul'

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
        logger.info(f"[handoff] debounce: '{task_id}' already scheduled by an earlier event in this burst")
        return {"status": "already_scheduled", "group_code": groupcode, "task_id": task_id, "fire_at_epoch": fire_at}
    except Exception as e:
        logger.error(f"[handoff] debounce: error scheduling task '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
