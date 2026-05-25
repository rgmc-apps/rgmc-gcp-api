"""Business Central Customer endpoints."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import (
    call_bc_table,
    bc_get_record,
    bc_create_record,
    bc_update_record,
    bc_delete_record,
)
from src.models.bc_models import CustomerCreate, CustomerUpdate

logger = logging.getLogger("bc_routes.customers")

customer_router = APIRouter(prefix="/bc/customers", tags=["BC Customers"])

_TABLE = "customers"


def _unwrap_list(bc_result: tuple) -> List[Dict[str, Any]]:
    http_status, data = bc_result
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data.get("value", data)


def _unwrap_single(http_status: int, data: Any) -> Dict[str, Any]:
    if http_status == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@customer_router.get("", summary="List Customers")
def list_customers(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. customerFinancialDetail)"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_bc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing customers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/{customer_id}", summary="Get Customer by ID")
def get_customer(
    customer_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. customerFinancialDetail)"),
):
    try:
        http_status, data = bc_get_record(_TABLE, customer_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.post("", summary="Create Customer", status_code=status.HTTP_201_CREATED)
def create_customer(
    body: CustomerCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        http_status, data = bc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.patch("/{customer_id}", summary="Update Customer")
def update_customer(
    customer_id: str,
    body: CustomerUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = bc_update_record(_TABLE, customer_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.delete("/{customer_id}", summary="Delete Customer", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(
    customer_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = bc_delete_record(_TABLE, customer_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
