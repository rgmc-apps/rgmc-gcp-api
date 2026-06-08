"""RGMC custom API — Item Price endpoints (Pag50210)."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import rgmc_list_item_prices

logger = logging.getLogger("bc_routes.rgmc_item_prices")

rgmc_item_price_router = APIRouter(prefix="/bc/custom/item-prices", tags=["BC RGMC Item Prices"])


def _unwrap(http_status: int, data: Any) -> List[Dict[str, Any]]:
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data.get("value", data)


@rgmc_item_price_router.get("", summary="List Item Prices")
def list_item_prices(
    product_no: Optional[str] = Query(None, description="Filter by item No. (productNo)"),
    on_date: Optional[str] = Query(None, description="Upper bound for startingDate (YYYY-MM-DD)"),
    filter: Optional[str] = Query(None, description="Additional OData $filter expression"),
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_list_item_prices(
            company_name=company,
            product_no=product_no,
            on_date=on_date,
            odata_filter=filter,
        )
        return {"data": _unwrap(http_status, data)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing item prices: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_item_price_router.get("/active", summary="Get Active Price for Item on Date")
def get_active_item_price(
    product_no: str = Query(..., description="Item No."),
    on_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    company: Optional[str] = Query(None, description="Override company name"),
):
    """Returns the single active price for an item on the given date.
    A price is active when startingDate <= on_date <= endingDate.
    A blank endingDate (stored as 0001-01-01 by BC) means open-ended — always included.
    Results are ordered by startingDate desc; $top=1 returns the most-recently-effective price."""
    try:
        http_status, data = rgmc_list_item_prices(
            company_name=company,
            product_no=product_no,
            on_date=on_date,
            top=1,
        )
        records = _unwrap(http_status, data)
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active price found for item '{product_no}' on {on_date}",
            )
        return records[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching active price for item {product_no} on {on_date}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
