"""CustomerPOULDetail (clean PO lines) read endpoints."""
import logging
from typing import Optional
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from src.routers.sbic_routes._db import run_query

# Instantiate a Cloud Logging client
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('customerpouldetail')

customerpouldetail_router = APIRouter(prefix="/customerpouldetail", tags=["CustomerPOULDetail"])


@customerpouldetail_router.get("", summary="List CustomerPOULDetail lines")
def list_customerpouldetail(
    po_ref_number: Optional[str] = Query(None, description="Exact poRefNumber match"),
    customer_id: Optional[int] = Query(None, description="Exact customerId match"),
    limit: int = Query(200, ge=1, le=2000),
):
    conditions: list[str] = []
    params: dict = {}
    if po_ref_number:
        conditions.append("poRefNumber = :po_ref_number")
        params["po_ref_number"] = po_ref_number
    if customer_id is not None:
        conditions.append("customerId = :customer_id")
        params["customer_id"] = customer_id
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = run_query(f"SELECT TOP {limit} * FROM CustomerPOULDetail {where}", params)
    return {"record_count": len(rows), "data": rows}


@customerpouldetail_router.get("/{po_ref_number}", summary="Get CustomerPOULDetail lines by PO ref number")
def get_customerpouldetail_by_ref(po_ref_number: str):
    rows = run_query(
        "SELECT * FROM CustomerPOULDetail WHERE poRefNumber = :po_ref_number",
        {"po_ref_number": po_ref_number},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerPOULDetail rows found for poRefNumber={po_ref_number!r}",
        )
    return {"record_count": len(rows), "data": rows}
