"""RGMC custom API — Item endpoints (Pag50205)."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import call_rgmc_table, rgmc_get_record

logger = logging.getLogger("bc_routes.rgmc_items")

rgmc_item_router = APIRouter(prefix="/bc/custom/items", tags=["BC RGMC Items"])

_TABLE = "items"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@rgmc_item_router.get("", summary="List RGMC Items")
def list_rgmc_items(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    select: Optional[str] = Query(None, description="OData $select"),
    category_code: Optional[str] = Query(None, description="Filter by itemCategoryCode"),
    family_code: Optional[str] = Query(None, description="Filter by familyCode"),
):
    try:
        odata_filter = filter
        if category_code:
            clause = f"itemCategoryCode eq '{category_code}'"
            odata_filter = f"({odata_filter}) and {clause}" if odata_filter else clause
        if family_code:
            clause = f"familyCode eq '{family_code}'"
            odata_filter = f"({odata_filter}) and {clause}" if odata_filter else clause
        result = call_rgmc_table(_TABLE, company_name=company, odata_filter=odata_filter, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing RGMC items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_item_router.get("/{item_id}", summary="Get RGMC Item by ID")
def get_rgmc_item(
    item_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_get_record(_TABLE, item_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching RGMC item {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
