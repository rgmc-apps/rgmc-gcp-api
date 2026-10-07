"""CustomerPOUL Related Queries and Functions."""
import json
import logging
import uuid
from typing import Optional
from google.cloud import logging as cloud_logging
from fastapi import HTTPException, Query, Request, status, Depends, APIRouter, Body
import src.config as config
from src.routers.bigquery_bridge import BigqueryBridge
from src.config import pass_key
from src.routers.sbic_routes.rate_limiter import rate_limit
from src.routers.sbic_routes._db import run_query
from src.services.bc_functions import call_bc_table, call_rgmc_table
from src.services.fuzzy_match import DEFAULT_THRESHOLD, best_matches

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('customerpoul')

customerpoul_router = APIRouter(prefix="/customerpoul", tags=["CustomerPOUL"])

# Company routing rule mirrored from the SO import worker (mssql_bc_mapping.txt §5):
# CustomerPOUL.companyName contains one of these keywords -> BC company code.
# Checked in order; first match wins.
_COMPANY_KEYWORD_MAP: list[tuple[str, str]] = [
    ("SUNCOAST", "SBIC"),
    ("SBIC", "SBIC"),
    ("MANILA", "MTC"),
    ("MTC", "MTC"),
]


def _resolve_bc_company(source_company_name: Optional[str]) -> Optional[str]:
    upper = (source_company_name or "").upper()
    for keyword, bc_company in _COMPANY_KEYWORD_MAP:
        if keyword in upper:
            return bc_company
    return None


def _get_latest_header(po_ref_number: str) -> dict:
    rows = run_query(
        "SELECT TOP 1 * FROM CustomerPOUL WHERE poRefNumber = :po_ref_number ORDER BY customerPOId DESC",
        {"po_ref_number": po_ref_number},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOUL row found for poRefNumber={po_ref_number!r}",
        )
    return rows[0]

@customerpoul_router.post(
    "/insert-from-bigquery",
    summary="Insert caller-picked int_document_ai/int_document_ai_detail rows into CustomerPOULBQ/CustomerPOULDetailBQ",
    dependencies=[Depends(rate_limit)],
)
async def insert_from_bigquery(
    headers: list = Body(..., description="int_document_ai rows (BigQuery/snake_case column names) to insert"),
    details: list = Body([], description="int_document_ai_detail rows (BigQuery/snake_case column names) belonging to those headers"),
):
    """Manual counterpart to /runbridge/ — instead of pulling everything new since the
    last automated run, inserts exactly the caller-selected rows (from the
    GET /bigquery_routes/document-ai/search results) into the same CustomerPOULBQ/
    CustomerPOULDetailBQ staging tables the automated bridge writes to, so the same
    AFTER INSERT trigger on the header table promotes them into CustomerPOUL/
    CustomerPOULDetail exactly as it would for an automated insert. Does NOT publish
    the SO-import Pub/Sub trigger — the manual-trigger page always routes these into
    the Firestore buffer separately for human review first, never an immediate
    automatic BC import attempt.
    """
    if not headers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="headers must not be empty")
    try:
        bridge = BigqueryBridge(logger, method="manual", group_code="customerpoul")
        return bridge.insert_selected_records(headers, details)
    except Exception as e:
        logger.error(f"Error inserting selected BigQuery records into MSSQL: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customerpoul_router.post("/runbridge/")
async def run_customerpoul_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='customerpoul')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customerpoul_router.post("/runbridge/onlinesalespo/")
async def run_online_sales_po_bridge(request: Request, method: str = 'manual'):
    try:
        bridge = BigqueryBridge(logger, method, group_code='onlinesalespo')
        result = bridge.main()
        return result
    except Exception as e:
        logger.error(f"Error running BigQuery bridge: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _publish_poul_so_message(msg_type: str, extra: dict, notify_name, notify_company, notify_department, notify_email) -> dict:
    """Shared publish path for every poul-so-* trigger message: attaches a run_id
    (tracked in Firestore reprocess_runs_{env} by rgmc-worker-pool, readable via
    rgmc-bc-api's GET /bc/custom/v2/so-buffer/reprocess-status/{run_id}) and an
    optional notify block (the employee to CC on the result emails).
    """
    topic = config.pubsub_poul_so_topic
    if not topic:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PUBSUB_POUL_SO_TOPIC is not configured",
        )
    try:
        from google.cloud import pubsub_v1
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google-cloud-pubsub is not installed",
        )

    run_id = uuid.uuid4().hex
    payload: dict = {"type": msg_type, "run_id": run_id, **extra}
    if notify_email:
        payload["notify"] = {
            "name": notify_name or "",
            "company": notify_company or "",
            "department": notify_department or "",
            "email": notify_email,
        }

    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(config.bigquery_project_id, topic)
        publisher.publish(topic_path, json.dumps(payload).encode("utf-8")).result(timeout=10)
    except Exception as e:
        logger.error(f"Error publishing {msg_type}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    return {"status": "triggered", "topic": topic, "run_id": run_id}


@customerpoul_router.post(
    "/reprocess-buffer",
    summary="Trigger a reprocess pass over the Firestore SO-import buffer (so_buffer_*)",
    dependencies=[Depends(rate_limit)],
)
def reprocess_buffer(
    companies: Optional[str] = Query(
        None, description="Comma-separated BC company codes to reprocess (e.g. SBIC,MTC). Omit to reprocess all."
    ),
    notify_name: Optional[str] = Query(None, description="Employee name to notify with the reprocess result"),
    notify_company: Optional[str] = Query(None, description="Employee's company, for the notification email"),
    notify_department: Optional[str] = Query(None, description="Employee's department, for the notification email"),
    notify_email: Optional[str] = Query(None, description="Employee email to CC on the reprocess result emails"),
):
    """Publish a poul-so-reprocess-buffer message to the same Pub/Sub topic the POUL SO
    import worker already subscribes to. The worker pulls every order currently sitting
    in its Firestore so_buffer_{env} collection for the given company/companies and
    retries BC Sales Order creation — the exact same retry path buffered orders already
    go through at the start of the next real batch, just triggered on demand instead of
    waiting for a new inbound PO.

    notify_* (all optional, but notify_email is what actually triggers a CC) identifies
    the person who triggered this from the /reconcile page — the worker pool includes
    notify_email on every result email for this run alongside its own developer alert
    address, so the requester sees the outcome directly.

    The response's run_id identifies this attempt in Firestore's reprocess_runs_{env}
    collection (written by rgmc-worker-pool as it processes the message) — poll
    rgmc-bc-api's GET /bc/custom/v2/so-buffer/reprocess-status/{run_id} to see whether
    it's still processing, done, or errored.
    """
    company_list = [c.strip().upper() for c in companies.split(",") if c.strip()] if companies else None
    result = _publish_poul_so_message(
        "poul-so-reprocess-buffer",
        {"companies": company_list} if company_list else {},
        notify_name, notify_company, notify_department, notify_email,
    )
    result["companies"] = company_list or "all"
    return result


@customerpoul_router.post(
    "/sync-inserted-orders",
    summary="Backfill lines onto already-inserted BC sales orders from Cloud SQL CustomerPOUL/CustomerPOULDetail",
    dependencies=[Depends(rate_limit)],
)
def sync_inserted_orders(
    companies: Optional[str] = Query(
        None, description="Comma-separated BC company codes to sync (e.g. SBIC,MTC). Omit to sync all."
    ),
    create_by: str = Query(
        "trigger", description="Only CustomerPOUL rows with this createBy are candidates (default 'trigger' — the BigQuery bridge's automated inserts)."
    ),
    notify_name: Optional[str] = Query(None, description="Employee name to notify with the sync result"),
    notify_company: Optional[str] = Query(None, description="Employee's company, for the notification email"),
    notify_department: Optional[str] = Query(None, description="Employee's department, for the notification email"),
    notify_email: Optional[str] = Query(None, description="Employee email to CC on the sync result emails"),
):
    """Publish a poul-so-sync-from-cloudsql message. The worker re-derives each
    candidate PO's lines from Cloud SQL (CustomerPOUL filtered by create_by, joined to
    CustomerPOULDetail by poRefNumber) and adds any that are missing from the BC sales
    order already created for it (found by externalDocumentNo) — the header is never
    recreated, only missing lines are added.

    This exists because the BigQuery bridge's header/detail join is a race: if a PO's
    detail rows land in BigQuery in a later incremental fetch than its header row, the
    SO import fires with zero lines and never revisits that header — Cloud SQL still
    has the real detail rows, this just re-syncs them onto the order that's missing
    them. Same run_id/notify tracking as /reprocess-buffer — poll
    rgmc-bc-api's GET /bc/custom/v2/so-buffer/reprocess-status/{run_id}.
    """
    company_list = [c.strip().upper() for c in companies.split(",") if c.strip()] if companies else None
    extra = {"create_by": create_by}
    if company_list:
        extra["companies"] = company_list
    result = _publish_poul_so_message(
        "poul-so-sync-from-cloudsql", extra,
        notify_name, notify_company, notify_department, notify_email,
    )
    result["companies"] = company_list or "all"
    result["create_by"] = create_by
    return result


@customerpoul_router.post(
    "/backfill-from-cloudsql",
    summary="Create missing BC sales orders from Cloud SQL CustomerPOUL/CustomerPOULDetail",
    dependencies=[Depends(rate_limit)],
)
def backfill_from_cloudsql(
    companies: Optional[str] = Query(
        None, description="Comma-separated BC company codes to backfill (e.g. SBIC,MTC). Omit to backfill all."
    ),
    create_by: str = Query(
        "trigger", description="Only CustomerPOUL rows with this createBy are candidates (default 'trigger' — the BigQuery bridge's automated inserts)."
    ),
    date_from: Optional[str] = Query(None, description="Only CustomerPOUL rows with createDate >= this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Only CustomerPOUL rows with createDate <= this date (YYYY-MM-DD)"),
    notify_name: Optional[str] = Query(None, description="Employee name to notify with the backfill result"),
    notify_company: Optional[str] = Query(None, description="Employee's company, for the notification email"),
    notify_department: Optional[str] = Query(None, description="Employee's department, for the notification email"),
    notify_email: Optional[str] = Query(None, description="Employee email to CC on the backfill result emails"),
):
    """Publish a poul-so-backfill-from-cloudsql message. For every CustomerPOUL row
    matching create_by (and, if given, the createDate range — when the row was
    inserted into CustomerPOUL, not poDate, the original PO date from the source
    ERP), the worker creates a FRESH
    BC sales order (header + lines) from CustomerPOUL/CustomerPOULDetailBQ — the
    opposite skip condition from /sync-inserted-orders, which only acts on a PO whose
    BC order already exists. Here, a PO whose externalDocumentNo already matches an
    existing BC sales order is skipped outright (never re-created, never touched).

    Any PO that can't be fully resolved (no ship-to/customer/item match, or BC itself
    rejects it) is buffered via the same Firestore so_buffer_{env} mechanism every
    other import path uses, so it shows up on /reconcile for manual reconciliation
    instead of silently failing. Same run_id/notify tracking as /reprocess-buffer and
    /sync-inserted-orders — poll rgmc-bc-api's
    GET /bc/custom/v2/so-buffer/reprocess-status/{run_id}.
    """
    company_list = [c.strip().upper() for c in companies.split(",") if c.strip()] if companies else None
    extra = {"create_by": create_by}
    if company_list:
        extra["companies"] = company_list
    if date_from:
        extra["date_from"] = date_from
    if date_to:
        extra["date_to"] = date_to
    result = _publish_poul_so_message(
        "poul-so-backfill-from-cloudsql", extra,
        notify_name, notify_company, notify_department, notify_email,
    )
    result["companies"] = company_list or "all"
    result["create_by"] = create_by
    result["date_from"] = date_from
    result["date_to"] = date_to
    return result


@customerpoul_router.get("", summary="List CustomerPOUL headers")
def list_customerpoul(
    po_ref_number: Optional[str] = Query(None, description="Exact poRefNumber match"),
    customer_name: Optional[str] = Query(None, description="Substring match on customerName"),
    customer_id: Optional[int] = Query(None, description="Exact customerId match"),
    po_status: Optional[str] = Query(None, description="Exact poStatus match"),
    company_name: Optional[str] = Query(None, description="Substring match on companyName"),
    company_id: Optional[int] = Query(None, description="Exact companyId match (e.g. SBIC=6, MTC=12 on sbic_prod)"),
    create_by: Optional[str] = Query(
        None, description="Exact createBy match — e.g. 'trigger' for rows auto-inserted by the BigQuery bridge"
    ),
    date_from: Optional[str] = Query(None, description="Only rows with createDate >= this date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Only rows with createDate <= this date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000),
):
    conditions: list[str] = []
    params: dict = {}
    if po_ref_number:
        conditions.append("poRefNumber = :po_ref_number")
        params["po_ref_number"] = po_ref_number
    if customer_name:
        conditions.append("customerName LIKE :customer_name")
        params["customer_name"] = f"%{customer_name}%"
    if customer_id is not None:
        conditions.append("customerId = :customer_id")
        params["customer_id"] = customer_id
    if company_id is not None:
        conditions.append("companyId = :company_id")
        params["company_id"] = company_id
    if po_status:
        conditions.append("poStatus = :po_status")
        params["po_status"] = po_status
    if company_name:
        conditions.append("companyName LIKE :company_name")
        params["company_name"] = f"%{company_name}%"
    if create_by:
        conditions.append("createBy = :create_by")
        params["create_by"] = create_by
    if date_from:
        conditions.append("createDate >= :date_from")
        params["date_from"] = date_from
    if date_to:
        # Inclusive of the whole end day — createDate is a datetime column, so a bare
        # "<= date_to" would exclude same-day rows with a non-midnight time component.
        conditions.append("createDate < DATEADD(day, 1, CAST(:date_to AS date))")
        params["date_to"] = date_to
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # ORDER BY createDate, not customerPOId: "re-PO" rows use customerPOId=-1 as a
    # sentinel, which sorted dead last under customerPOId DESC and silently fell outside
    # the TOP {limit} window on every caller (sync, backfill) regardless of recency.
    rows = run_query(f"SELECT TOP {limit} * FROM CustomerPOUL {where} ORDER BY createDate DESC", params)
    return {"record_count": len(rows), "data": rows}


@customerpoul_router.get("/{po_ref_number}", summary="Get CustomerPOUL header(s) by PO ref number")
def get_customerpoul_by_ref(po_ref_number: str):
    rows = run_query(
        "SELECT * FROM CustomerPOUL WHERE poRefNumber = :po_ref_number ORDER BY customerPOId DESC",
        {"po_ref_number": po_ref_number},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOUL row found for poRefNumber={po_ref_number!r}",
        )
    return {"record_count": len(rows), "data": rows}


@customerpoul_router.get(
    "/{po_ref_number}/shipto-match",
    summary="Fuzzy-match this PO's customerBranchName to a BC Ship-To Address",
)
def match_shipto(
    po_ref_number: str,
    company: Optional[str] = Query(None, description="Override BC company (defaults to routing from companyName)"),
    threshold: float = Query(DEFAULT_THRESHOLD, ge=0.0, le=1.0, description="Minimum fuzzy score to include a match"),
    top: int = Query(5, ge=1, le=20, description="Max number of fuzzy candidates to return"),
):
    header = _get_latest_header(po_ref_number)
    branch_name = header.get("customerBranchName") or ""
    branch_code = (header.get("customerBranchLookUpCode") or "").strip()

    bc_company = company or _resolve_bc_company(header.get("companyName"))
    if not bc_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve a BC company from companyName={header.get('companyName')!r}; pass ?company=",
        )

    try:
        http_status, data = call_rgmc_table("shipToAddresses", company_name=bc_company, api_version="v2.0")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BC ship-to addresses for {bc_company}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    if http_status != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"BC returned {http_status}: {data}")
    ship_tos = data.get("value", [])

    exact_code_match = None
    if branch_code:
        for ship_to in ship_tos:
            if (ship_to.get("code") or "").strip().upper() == branch_code.upper():
                exact_code_match = ship_to
                break

    candidates = [(ship_to.get("name") or "", ship_to) for ship_to in ship_tos]
    matches = best_matches(branch_name, candidates, threshold=threshold, top_n=top)

    return {
        "poRefNumber": po_ref_number,
        "customerBranchName": branch_name,
        "customerBranchLookUpCode": branch_code,
        "bcCompany": bc_company,
        "exactCodeMatch": exact_code_match,
        "fuzzyMatches": matches,
    }


@customerpoul_router.get(
    "/{po_ref_number}/item-match",
    summary="Fuzzy-match this PO's line customerSKUDesc values to BC Items",
)
def match_items(
    po_ref_number: str,
    company: Optional[str] = Query(None, description="Override BC company (defaults to routing from companyName)"),
    threshold: float = Query(DEFAULT_THRESHOLD, ge=0.0, le=1.0, description="Minimum fuzzy score to include a match"),
    top: int = Query(3, ge=1, le=20, description="Max number of fuzzy candidates to return per line"),
):
    header = _get_latest_header(po_ref_number)
    lines = run_query(
        "SELECT * FROM CustomerPOULDetail WHERE poRefNumber = :po_ref_number",
        {"po_ref_number": po_ref_number},
    )
    if not lines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOULDetail rows found for poRefNumber={po_ref_number!r}",
        )

    bc_company = company or _resolve_bc_company(header.get("companyName"))
    if not bc_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve a BC company from companyName={header.get('companyName')!r}; pass ?company=",
        )

    try:
        http_status, data = call_bc_table(
            "items", company_name=bc_company, select="number,displayName,displayName2,blocked"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching BC items for {bc_company}: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    if http_status != 200:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"BC returned {http_status}: {data}")
    items = data.get("value", [])
    candidates = [(item.get("displayName") or "", item) for item in items]

    results = []
    for line in lines:
        sku_desc = line.get("customerSKUDesc") or ""
        results.append({
            "customerSKUCode": line.get("customerSKUCode"),
            "customerSKUDesc": sku_desc,
            "fuzzyMatches": best_matches(sku_desc, candidates, threshold=threshold, top_n=top),
        })

    return {"poRefNumber": po_ref_number, "bcCompany": bc_company, "lines": results}