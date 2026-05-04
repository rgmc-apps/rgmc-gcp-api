"""Trade Portal Pull Out Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import StockPullOut, StockPullOutDetail, StockPullOutRequest, SMPullOut, SMPullOutDetail
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.pullout')

pullout_router = APIRouter(tags=["Trade Portal"])


@pullout_router.get("/stock-pullouts", response_model=List[StockPullOut])
def get_stock_pullouts(customer_id: Optional[int] = None, source_brand_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if source_brand_id is not None:
            conditions.append("sourceBrandId = :source_brand_id")
            params["source_brand_id"] = source_brand_id
        query = "SELECT * FROM dbo.StockPullOut"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [StockPullOut(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching StockPullOuts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pullout_router.get("/stock-pullouts/{stock_pullout_id}", response_model=StockPullOut)
def get_stock_pullout(stock_pullout_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.StockPullOut WHERE stockPullOutId = :stock_pullout_id"),
                {"stock_pullout_id": stock_pullout_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="StockPullOut not found")
        return StockPullOut(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching StockPullOut {stock_pullout_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pullout_router.get("/stock-pullout-details", response_model=List[StockPullOutDetail])
def get_stock_pullout_details(stock_pullout_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.StockPullOutDetail"
        if stock_pullout_id is not None:
            query += " WHERE stockPullOutId = :stock_pullout_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"stock_pullout_id": stock_pullout_id} if stock_pullout_id is not None else {}).fetchall()
            return [StockPullOutDetail(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching StockPullOutDetails: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pullout_router.get("/stock-pullout-requests", response_model=List[StockPullOutRequest])
def get_stock_pullout_requests(brand_id: Optional[int] = None, store_id: Optional[int] = None, request_status: Optional[str] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if store_id is not None:
            conditions.append("storeId = :store_id")
            params["store_id"] = store_id
        if request_status is not None:
            conditions.append("requestStatus = :request_status")
            params["request_status"] = request_status
        query = "SELECT * FROM dbo.StockPullOutRequest"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [StockPullOutRequest(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching StockPullOutRequests: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pullout_router.get("/sm-pullouts", response_model=List[SMPullOut])
def get_sm_pullouts(site_id: Optional[int] = None, source_brand_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        if source_brand_id is not None:
            conditions.append("sourceBrandId = :source_brand_id")
            params["source_brand_id"] = source_brand_id
        query = "SELECT * FROM dbo.SMPullOut"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMPullOut(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMPullOuts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@pullout_router.get("/sm-pullout-details", response_model=List[SMPullOutDetail])
def get_sm_pullout_details(site_id: Optional[int] = None, sm_pullout_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        if sm_pullout_id is not None:
            conditions.append("smPullOutId = :sm_pullout_id")
            params["sm_pullout_id"] = sm_pullout_id
        query = "SELECT * FROM dbo.SMPullOutDetail"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMPullOutDetail(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMPullOutDetails: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
