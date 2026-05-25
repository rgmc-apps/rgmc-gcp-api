"""Business Central Item endpoints."""
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
from src.models.bc_models import ItemCreate, ItemUpdate

logger = logging.getLogger("bc_routes.items")

item_router = APIRouter(prefix="/bc/items", tags=["BC Items"])

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
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@item_router.get("", summary="List Items")
def list_items(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. itemVariants)"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_bc_table(_TABLE, company_name=company, odata_filter=filter, expand=expand, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@item_router.get("/{item_id}", summary="Get Item by ID")
def get_item(
    item_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
    expand: Optional[str] = Query(None, description="OData $expand (e.g. itemVariants)"),
):
    try:
        http_status, data = bc_get_record(_TABLE, item_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching item {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@item_router.post("", summary="Create Item", status_code=status.HTTP_201_CREATED)
def create_item(
    body: ItemCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        http_status, data = bc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@item_router.patch("/{item_id}", summary="Update Item")
def update_item(
    item_id: str,
    body: ItemUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = bc_update_record(_TABLE, item_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating item {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@item_router.delete("/{item_id}", summary="Delete Item", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = bc_delete_record(_TABLE, item_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting item {item_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
