"""RGMC custom API — Retail Customer endpoints (Pag50200)."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import (
    call_rgmc_table,
    rgmc_get_record,
    rgmc_create_record,
    rgmc_update_record,
    rgmc_delete_record,
)
from src.models.bc_models import RetailCustomerCreate, RetailCustomerUpdate

logger = logging.getLogger("bc_routes.retail_customers")

retail_customer_router = APIRouter(prefix="/bc/custom/retail-customers", tags=["BC RGMC Retail Customers"])

_TABLE = "retailCustomers"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retail customer not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@retail_customer_router.get("", summary="List Retail Customers")
def list_retail_customers(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_rgmc_table(_TABLE, company_name=company, odata_filter=filter, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing retail customers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@retail_customer_router.get("/{customer_id}", summary="Get Retail Customer by ID")
def get_retail_customer(
    customer_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_get_record(_TABLE, customer_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching retail customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@retail_customer_router.post("", summary="Create Retail Customer", status_code=status.HTTP_201_CREATED)
def create_retail_customer(
    body: RetailCustomerCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        http_status, data = rgmc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating retail customer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@retail_customer_router.patch("/{customer_id}", summary="Update Retail Customer")
def update_retail_customer(
    customer_id: str,
    body: RetailCustomerUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = rgmc_update_record(_TABLE, customer_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retail customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@retail_customer_router.delete("/{customer_id}", summary="Delete Retail Customer", status_code=status.HTTP_204_NO_CONTENT)
def delete_retail_customer(
    customer_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = rgmc_delete_record(_TABLE, customer_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retail customer not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting retail customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
