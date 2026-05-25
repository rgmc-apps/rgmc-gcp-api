"""Business Central Sales Credit Memo endpoints (sales return equivalent)."""
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
from src.models.bc_models import SalesCreditMemoCreate, SalesCreditMemoUpdate

logger = logging.getLogger("bc_routes.sales_credit_memos")

sales_credit_memo_router = APIRouter(prefix="/bc/sales-credit-memos", tags=["BC Sales Credit Memos"])

_TABLE = "salesCreditMemos"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales credit memo not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@sales_credit_memo_router.get("", summary="List Sales Credit Memos")
def list_sales_credit_memos(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesCreditMemoLines)"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_bc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing sales credit memos: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_credit_memo_router.get("/{memo_id}", summary="Get Sales Credit Memo by ID")
def get_sales_credit_memo(
    memo_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. salesCreditMemoLines)"),
):
    try:
        http_status, data = bc_get_record(_TABLE, memo_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales credit memo {memo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_credit_memo_router.post("", summary="Create Sales Credit Memo", status_code=status.HTTP_201_CREATED)
def create_sales_credit_memo(
    body: SalesCreditMemoCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        http_status, data = bc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating sales credit memo: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_credit_memo_router.patch("/{memo_id}", summary="Update Sales Credit Memo")
def update_sales_credit_memo(
    memo_id: str,
    body: SalesCreditMemoUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = bc_update_record(_TABLE, memo_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sales credit memo {memo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sales_credit_memo_router.delete("/{memo_id}", summary="Delete Sales Credit Memo", status_code=status.HTTP_204_NO_CONTENT)
def delete_sales_credit_memo(
    memo_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = bc_delete_record(_TABLE, memo_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sales credit memo not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting sales credit memo {memo_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
