"""Trade Portal Location Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import Site, StoreType, Store, SMStore
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.location')

location_router = APIRouter(tags=["Trade Portal"])


@location_router.get("/sites", response_model=List[Site])
def get_sites():
    try:
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text("SELECT * FROM dbo.Site")).fetchall()
            return [Site(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching sites: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/sites/{site_id}", response_model=Site)
def get_site(site_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Site WHERE siteId = :site_id"),
                {"site_id": site_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
        return Site(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching site {site_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/store-types", response_model=List[StoreType])
def get_store_types(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.StoreType"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [StoreType(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching StoreTypes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/store-types/{store_type_id}", response_model=StoreType)
def get_store_type(store_type_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.StoreType WHERE storeTypeId = :store_type_id"),
                {"store_type_id": store_type_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StoreType not found")
        return StoreType(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching StoreType {store_type_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/stores", response_model=List[Store])
def get_stores(
    customer_id: Optional[int] = None,
    brand_id: Optional[int] = None,
    customer_site_id: Optional[int] = None,
    is_active: Optional[bool] = None,
):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if customer_site_id is not None:
            conditions.append("customerSiteId = :customer_site_id")
            params["customer_site_id"] = customer_site_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.Store"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [Store(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching stores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/stores/{store_id}", response_model=Store)
def get_store(store_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Store WHERE storeId = :store_id"),
                {"store_id": store_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")
        return Store(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching store {store_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/sm-stores", response_model=List[SMStore])
def get_sm_stores(customer_site_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if customer_site_id is not None:
            conditions.append("customerSiteId = :customer_site_id")
            params["customer_site_id"] = customer_site_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.SMStore"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMStore(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMStores: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@location_router.get("/sm-stores/{sm_store_code}", response_model=SMStore)
def get_sm_store(sm_store_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SMStore WHERE smStoreCode = :sm_store_code"),
                {"sm_store_code": sm_store_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMStore not found")
        return SMStore(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SMStore {sm_store_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
