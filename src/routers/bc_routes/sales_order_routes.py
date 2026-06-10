"""Business Central Sales Order endpoints (RGMC custom API — Pag50216/50217)."""
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
from src.models.bc_models import SalesOrderCreate, SalesOrderUpdate, SalesOrderLineCreate, SalesOrderLineUpdate

logger = logging.getLogger("bc_routes.sales_orders")

sales_order_router = APIRouter(prefix="/bc/sales-orders", tags=["BC Sales Orders"])

_TABLE = "salesOrders"
_LINES_TABLE = "salesOrderLines"


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
        result = call_rgmc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
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
        http_status, data = rgmc_get_record(_TABLE, order_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def _map_line_payload(line: dict) -> dict:
    """Map frontend line fields to RGMC custom salesOrderLines field names (Pag50217)."""
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


@sales_order_router.post("", summary="Create Sales Order", status_code=status.HTTP_201_CREATED)
def create_sales_order(
    body: SalesOrderCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)

        # Map frontend field names to RGMC custom API field names
        if 'customerNumber' in payload:
            payload['sellToCustomerNo'] = payload.pop('customerNumber')
        if 'externalDocumentNumber' in payload:
            payload['externalDocumentNo'] = payload.pop('externalDocumentNumber')

        # Lines are not a header field — extract before POSTing the header
        lines = payload.pop('lines', [])

        http_status, data = rgmc_create_record(_TABLE, payload, company_name=company)
        order = _unwrap_single(http_status, data)

        if lines:
            order_id = order.get('id')
            for i, line in enumerate(lines, start=1):
                try:
                    line_payload = _map_line_payload(line)
                    lh, ld = rgmc_create_record(
                        f"{_TABLE}({order_id})/{_LINES_TABLE}",
                        line_payload,
                        company_name=company,
                    )
                    if lh not in (200, 201):
                        raise ValueError(f"BC returned {lh}: {ld}")
                except Exception as line_err:
                    logger.error(f"Failed to create line {i} for sales order {order_id}: {line_err}")
                    # Roll back: delete the header so BC is not left with a partial order
                    try:
                        rgmc_delete_record(_TABLE, order_id, company_name=company)
                    except Exception as del_err:
                        logger.error(f"Rollback failed for sales order {order_id}: {del_err}")
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Line {i} creation failed: {line_err}. Order rolled back.",
                    )

        return order
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
        if 'customerNumber' in payload:
            payload['sellToCustomerNo'] = payload.pop('customerNumber')
        if 'externalDocumentNumber' in payload:
            payload['externalDocumentNo'] = payload.pop('externalDocumentNumber')
        http_status, data = rgmc_update_record(_TABLE, order_id, payload, company_name=company)
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
        http_status = rgmc_delete_record(_TABLE, order_id, company_name=company)
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


# ---------------------------------------------------------------------------
# Sales Order Lines
# ---------------------------------------------------------------------------

@sales_order_router.get("/{order_id}/lines", summary="List Lines for a Sales Order")
def list_sales_order_lines(
    order_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        result = call_rgmc_table(nested, company_name=company, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing lines for sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.post("/{order_id}/lines", summary="Create a Sales Order Line", status_code=status.HTTP_201_CREATED)
def create_sales_order_line(
    order_id: str,
    body: SalesOrderLineCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status, data = rgmc_create_record(nested, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating line for sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.patch("/{order_id}/lines/{line_id}", summary="Update a Sales Order Line")
def update_sales_order_line(
    order_id: str,
    line_id: str,
    body: SalesOrderLineUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(mode='json', exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status, data = rgmc_update_record(nested, line_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating line {line_id} for sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_order_router.delete("/{order_id}/lines/{line_id}", summary="Delete a Sales Order Line", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_order_line(
    order_id: str,
    line_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        nested = f"{_TABLE}({order_id})/{_LINES_TABLE}"
        http_status = rgmc_delete_record(nested, line_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales order line not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting line {line_id} for sales order {order_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
