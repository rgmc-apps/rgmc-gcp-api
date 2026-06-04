"""RGMC custom API — Sales Return Order endpoints (Pag50201 / Pag50202)."""
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
from src.models.bc_models import (
    SalesReturnOrderCreate,
    SalesReturnOrderUpdate,
    SalesReturnOrderLineCreate,
    SalesReturnOrderLineUpdate,
)

logger = logging.getLogger("bc_routes.sales_return_orders")

sales_return_order_router = APIRouter(prefix="/bc/custom/sales-return-orders", tags=["BC RGMC Sales Return Orders"])

_TABLE = "salesReturnOrders"
_LINES_TABLE = "salesReturnOrderLines"


def _unwrap_list(bc_result: tuple) -> List[Dict[str, Any]]:
    http_status, data = bc_result
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data.get("value", data)


def _unwrap_single(http_status: int, data: Any, label: str = "Record") -> Dict[str, Any]:
    if http_status == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


# ---------------------------------------------------------------------------
# Sales Return Orders
# ---------------------------------------------------------------------------

@sales_return_order_router.get("", summary="List Sales Return Orders")
def list_sales_return_orders(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesReturnOrderLines)"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_rgmc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sales return orders: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.get("/{order_id}", summary="Get Sales Return Order by ID")
def get_sales_return_order(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesReturnOrderLines)"),
):
    try:
        http_status, data = rgmc_get_record(_TABLE, order_id, company_name=company)
        return _unwrap_single(http_status, data, "Sales return order")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _map_line_payload(line: dict) -> dict:
    """Map frontend line fields to BC salesReturnOrderLines field names."""
    mapped: dict = {"lineType": "Item"}
    if "itemNumber" in line:
        mapped["number"] = line["itemNumber"]
    if "description" in line:
        mapped["description"] = line["description"]
    if "quantity" in line:
        mapped["quantity"] = line["quantity"]
    if "unitPrice" in line:
        mapped["unitPrice"] = line["unitPrice"]
    if "discountPercent" in line:
        mapped["lineDiscountPercent"] = line["discountPercent"]
    elif "lineDiscountAmount" in line:
        qty = line.get("quantity") or 1
        unit_price = line.get("unitPrice") or 0
        base = unit_price * qty
        if base > 0:
            mapped["lineDiscountPercent"] = round((line["lineDiscountAmount"] / base) * 100, 5)
    return mapped


@sales_return_order_router.post("", summary="Create Sales Return Order", status_code=status.HTTP_201_CREATED)
def create_sales_return_order(
    body: SalesReturnOrderCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)

        # Map frontend's `customerNumber` to BC's `sellToCustomerNo`
        if 'customerNumber' in payload:
            payload['sellToCustomerNo'] = payload.pop('customerNumber')

        # Lines are not a header field — extract before POSTing the header
        lines = payload.pop('lines', [])

        http_status, data = rgmc_create_record(_TABLE, payload, company_name=company)
        order = _unwrap_single(http_status, data, "Sales return order")

        if lines:
            order_id = order.get('id')
            for line in lines:
                line_payload = _map_line_payload(line)
                lh, ld = rgmc_create_record(
                    f"{_TABLE}({order_id})/{_LINES_TABLE}",
                    line_payload,
                    company_name=company,
                )
                if lh not in (200, 201):
                    logger.error(f"Failed to create line for return order {order_id}: {ld}")

        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sales return order: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.patch("/{order_id}", summary="Update Sales Return Order")
def update_sales_return_order(
    order_id: str,
    body: SalesReturnOrderUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = rgmc_update_record(_TABLE, order_id, payload, company_name=company)
        return _unwrap_single(http_status, data, "Sales return order")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.delete("/{order_id}", summary="Delete Sales Return Order", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_return_order(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = rgmc_delete_record(_TABLE, order_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales return order not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ---------------------------------------------------------------------------
# Sales Return Order Lines (nested under a parent order)
# ---------------------------------------------------------------------------

@sales_return_order_router.get("/{order_id}/lines", summary="List Lines for a Sales Return Order")
def list_sales_return_order_lines(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        result = call_rgmc_table(nested, company_name=company, odata_filter=filter, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing lines for sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.get("/{order_id}/lines/{line_id}", summary="Get a Sales Return Order Line by ID")
def get_sales_return_order_line(
    order_id: str,
    line_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status, data = rgmc_get_record(nested, line_id, company_name=company)
        return _unwrap_single(http_status, data, "Sales return order line")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching line {line_id} for sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.post("/{order_id}/lines", summary="Create a Sales Return Order Line", status_code=status.HTTP_201_CREATED)
def create_sales_return_order_line(
    order_id: str,
    body: SalesReturnOrderLineCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        payload = body.model_dump(exclude_none=True)
        http_status, data = rgmc_create_record(nested, payload, company_name=company)
        return _unwrap_single(http_status, data, "Sales return order line")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating line for sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.patch("/{order_id}/lines/{line_id}", summary="Update a Sales Return Order Line")
def update_sales_return_order_line(
    order_id: str,
    line_id: str,
    body: SalesReturnOrderLineUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status, data = rgmc_update_record(nested, line_id, payload, company_name=company)
        return _unwrap_single(http_status, data, "Sales return order line")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating line {line_id} for sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_return_order_router.delete("/{order_id}/lines/{line_id}", summary="Delete a Sales Return Order Line", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_return_order_line(
    order_id: str,
    line_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status = rgmc_delete_record(nested, line_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales return order line not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting line {line_id} for sales return order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
