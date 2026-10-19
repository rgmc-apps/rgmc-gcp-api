"""Publishes a "run the BigQuery bridge" request instead of running it inline.

The BigQuery-read + MSSQL-write work (BigqueryBridge.main()) used to run synchronously
inside whichever HTTP route received the request: /handoff/runbridge/ (Eventarc/Cloud-
Tasks-triggered, the automated path) and the three manual "Run Bridge Now" buttons on
sbic-manual-trigger-page's /trigger page (/customerpoul/runbridge/, .../runbridge/
onlinesalespo/, /customerra/runbridge/). That tied up a Cloud Run request/instance for
however long the BigQuery read + MSSQL write + SO-import publish took -- confirmed live
to run well past 30s under normal conditions, much longer during this project's
BigQuery/MSSQL slowdowns -- and was the backdrop for this session's whole concurrency/
rate-limiter saga (see this repo's handoff.md).

rgmc-worker-pool's Pub/Sub pull worker (src/workers/bigquery_bridge_worker.py) now does
the actual work, using flow_control=FlowControl(max_messages=1) for genuine mutual
exclusion -- a real improvement over the time-based rate limiter this repo's own
/handoff/runbridge/ still keeps in front of this publish call, purely as cheap defense-
in-depth against a misbehaving trigger spamming publishes.

insert_selected_records (the BigQuery Lookup tab's manual, caller-scoped insert of a
specific set of rows) is unaffected by this change -- it's never the heavy "everything
new since the last run" pull this module exists to get off this service's request path,
so it still runs inline here via BigqueryBridge directly, same as before.
"""
import json
import logging

from fastapi import HTTPException, status
from google.cloud import pubsub_v1

import src.config as config

logger = logging.getLogger("bridge_trigger")
_publisher = pubsub_v1.PublisherClient()


def publish_bridge_run(group_code: str, method: str = "manual") -> dict:
    """Publish {"group_code", "method"} to PUBSUB_BRIDGE_RUN_TOPIC and return
    immediately. Raises HTTPException (503/502) on failure, matching the shape every
    other Pub/Sub-publishing route in this repo already uses (see handoff.py's
    _publish_poul_so_message)."""
    topic = config.pubsub_bridge_run_topic
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PUBSUB_BRIDGE_RUN_TOPIC is not configured",
        )
    payload = {"group_code": group_code, "method": method}
    try:
        topic_path = _publisher.topic_path(config.bigquery_project_id, topic)
        _publisher.publish(topic_path, json.dumps(payload).encode("utf-8")).result(timeout=10)
    except Exception as e:
        logger.error(f"Error publishing bridge run request {payload}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    logger.info(f"Published bridge run request: {payload}")
    return {"status": "queued", "group_code": group_code, "method": method, "topic": topic}
