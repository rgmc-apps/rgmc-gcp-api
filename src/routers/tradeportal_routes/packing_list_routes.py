"""Trade Portal Packing List Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import PackingList, PackingListDetail, SMDR, SMPackingList
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.packlist')

packing_list_router = APIRouter(tags=["Trade Portal"])


@packing_list_router.get("/packing-lists", response_model=List[PackingList])
def get_packing_lists(customer_id: Optional[int] = None, brand_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        query = "SELECT * FROM dbo.PackingList"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [PackingList(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching PackingLists: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@packing_list_router.get("/packing-lists/{packing_list_id}", response_model=PackingList)
def get_packing_list(packing_list_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.PackingList WHERE packingListId = :packing_list_id"),
                {"packing_list_id": packing_list_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PackingList not found")
        return PackingList(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PackingList {packing_list_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@packing_list_router.get("/packing-list-details", response_model=List[PackingListDetail])
def get_packing_list_details(packing_list_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.PackingListDetail"
        if packing_list_id is not None:
            query += " WHERE packingListId = :packing_list_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"packing_list_id": packing_list_id} if packing_list_id is not None else {}).fetchall()
            return [PackingListDetail(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching PackingListDetails: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@packing_list_router.get("/sm-drs", response_model=List[SMDR])
def get_sm_drs(brand_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.SMDR"
        if brand_id is not None:
            query += " WHERE brandId = :brand_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"brand_id": brand_id} if brand_id is not None else {}).fetchall()
            return [SMDR(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMDRs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@packing_list_router.get("/sm-packing-lists", response_model=List[SMPackingList])
def get_sm_packing_lists(brand_id: Optional[int] = None, site_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        query = "SELECT * FROM dbo.SMPackingList"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMPackingList(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMPackingLists: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
