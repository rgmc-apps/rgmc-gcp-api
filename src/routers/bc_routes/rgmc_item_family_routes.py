"""RGMC custom API — Item Family endpoints (Pag50206)."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import call_rgmc_table, rgmc_get_record

logger = logging.getLogger("bc_routes.rgmc_item_families")

rgmc_item_family_router = APIRouter(prefix="/bc/custom/item-families", tags=["BC RGMC Item Families"])

_TABLE = "itemFamilies"


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item family not found")
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@rgmc_item_family_router.get("", summary="List RGMC Item Families")
def list_rgmc_item_families(
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
        logger.error(f"Error listing RGMC item families: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_item_family_router.get("/{family_id}", summary="Get RGMC Item Family by ID")
def get_rgmc_item_family(
    family_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_get_record(_TABLE, family_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching RGMC item family {family_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
