"""Trade Portal Brand Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import text
from src.models.tradeportal_models import Brand, BrandLookUpSM, KCCBrandLookUp, SMBrandSubClass, LMBrandSiteLookUp
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.brand')

brand_router = APIRouter(tags=["Trade Portal"])


@brand_router.get("/brands", response_model=List[Brand])
def get_brands(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.Brand"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [Brand(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@brand_router.get("/brands/{brand_id}", response_model=Brand)
def get_brand(brand_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Brand WHERE brandId = :brand_id"),
                {"brand_id": brand_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
        return Brand(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brand {brand_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@brand_router.get("/brand-lookups-sm", response_model=List[BrandLookUpSM])
def get_brand_lookups_sm(brand_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.BrandLookUpSM"
        if brand_id is not None:
            query += " WHERE brandId = :brand_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"brand_id": brand_id} if brand_id is not None else {}).fetchall()
            return [BrandLookUpSM(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching BrandLookUpSM: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@brand_router.get("/kcc-brand-lookups", response_model=List[KCCBrandLookUp])
def get_kcc_brand_lookups(brand_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.KCCBrandLookUp"
        if brand_id is not None:
            query += " WHERE brandId = :brand_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"brand_id": brand_id} if brand_id is not None else {}).fetchall()
            return [KCCBrandLookUp(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching KCCBrandLookUp: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@brand_router.get("/sm-brand-subclasses", response_model=List[SMBrandSubClass])
def get_sm_brand_subclasses(brand_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.SMBrandSubClass"
        if brand_id is not None:
            query += " WHERE brandId = :brand_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"brand_id": brand_id} if brand_id is not None else {}).fetchall()
            return [SMBrandSubClass(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMBrandSubClass: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@brand_router.get("/lm-brand-site-lookups", response_model=List[LMBrandSiteLookUp])
def get_lm_brand_site_lookups(brand_id: Optional[int] = None, customer_site_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if customer_site_id is not None:
            conditions.append("customerSiteId = :customer_site_id")
            params["customer_site_id"] = customer_site_id
        query = "SELECT * FROM dbo.LMBrandSiteLookUp"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [LMBrandSiteLookUp(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching LMBrandSiteLookUp: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
