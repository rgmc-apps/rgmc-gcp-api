"""CustomerBranch (sbic_prod master data) read endpoints.

Documented columns per mssql_bc_mapping.txt §3: customerBranchId, customerId, lookUpCode.
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

logger = logging.getLogger('sbic_customer_branch')

sbic_customer_branch_router = APIRouter(prefix="/sbic/customerbranches", tags=["SBIC Customer Branches"])


@sbic_customer_branch_router.get("", summary="List SBIC Customer Branches")
def list_sbic_customer_branches(
    customer_branch_id: Optional[int] = Query(None, description="Exact customerBranchId match"),
    customer_id: Optional[int] = Query(None, description="Exact customerId match"),
    lookup_code: Optional[str] = Query(None, description="Substring match on lookUpCode"),
    limit: int = Query(100, ge=1, le=1000),
):
    conditions: list[str] = []
    params: dict = {}
    if customer_branch_id is not None:
        conditions.append("customerBranchId = :customer_branch_id")
        params["customer_branch_id"] = customer_branch_id
    if customer_id is not None:
        conditions.append("customerId = :customer_id")
        params["customer_id"] = customer_id
    if lookup_code:
        conditions.append("lookUpCode LIKE :lookup_code")
        params["lookup_code"] = f"%{lookup_code}%"
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = run_query(f"SELECT TOP {limit} * FROM CustomerBranch {where}", params)
    return {"record_count": len(rows), "data": rows}


@sbic_customer_branch_router.get("/{customer_branch_id}", summary="Get SBIC Customer Branch by ID")
def get_sbic_customer_branch(customer_branch_id: int):
    rows = run_query(
        "SELECT * FROM CustomerBranch WHERE customerBranchId = :customer_branch_id",
        {"customer_branch_id": customer_branch_id},
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No CustomerBranch with customerBranchId={customer_branch_id}",
        )
    return rows[0]
