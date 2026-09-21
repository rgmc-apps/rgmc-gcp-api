"""Customer (sbic_prod master data) read endpoints.

Documented columns per mssql_bc_mapping.txt §3: customerId, lookUpCode, isActive.
Rows are returned as-is (SELECT *) so any additional columns on the live table are
included without needing this code to know every column name up front.
"""
import logging
from typing import Optional
from google.cloud import logging as cloud_logging
from fastapi import APIRouter, HTTPException, Query, status
from src.routers.sbic_routes._db import run_query

client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger('sbic_customer')

sbic_customer_router = APIRouter(prefix="/sbic/customers", tags=["SBIC Customers"])


@sbic_customer_router.get("", summary="List SBIC Customers")
def list_sbic_customers(
    customer_id: Optional[int] = Query(None, description="Exact customerId match"),
    lookup_code: Optional[str] = Query(None, description="Substring match on lookUpCode"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    conditions: list[str] = []
    params: dict = {}
    if customer_id is not None:
        conditions.append("customerId = :customer_id")
        params["customer_id"] = customer_id
    if lookup_code:
        conditions.append("lookUpCode LIKE :lookup_code")
        params["lookup_code"] = f"%{lookup_code}%"
    if is_active is not None:
        conditions.append("isActive = :is_active")
        params["is_active"] = is_active
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = run_query(f"SELECT TOP {limit} * FROM Customer {where}", params)
    return {"record_count": len(rows), "data": rows}


@sbic_customer_router.get("/{customer_id}", summary="Get SBIC Customer by ID")
def get_sbic_customer(customer_id: int):
    rows = run_query("SELECT * FROM Customer WHERE customerId = :customer_id", {"customer_id": customer_id})
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Customer with customerId={customer_id}")
    return rows[0]
