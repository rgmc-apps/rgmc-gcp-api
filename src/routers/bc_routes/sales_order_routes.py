"""Business Central Sales Order endpoints."""
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
from src.models.bc_models import SalesOrderCreate, SalesOrderUpdate

logger = logging.getLogger("bc_routes.sales_orders")

sales_order_router = APIRouter(prefix="/bc/sales-orders", tags=["BC Sales Orders"])

_TABLE = "salesOrders"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@sales_order_router.get("", summary="List Sales Orders")
def list_sales_orders(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesOrderLines)"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_bc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sales orders: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.get("/{order_id}", summary="Get Sales Order by ID")
def get_sales_order(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesOrderLines)"),
):
    try:
        table = f"{_TABLE}({order_id})"
        if expand:
            table += f"?$expand={expand}"
        http_status, data = bc_get_record(_TABLE, order_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.post("", summary="Create Sales Order", status_code=status.HTTP_201_CREATED)
def create_sales_order(
    body: SalesOrderCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)
        http_status, data = bc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sales order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.patch("/{order_id}", summary="Update Sales Order")
def update_sales_order(
    order_id: str,
    body: SalesOrderUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = bc_update_record(_TABLE, order_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.delete("/{order_id}", summary="Delete Sales Order", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_order(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = bc_delete_record(_TABLE, order_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
