"""Trade Portal SKU Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import KCCSKU, LMSKU, MGSKU, RDSSKU, RDSSaleSKU, SMSKU, SMSKURequest, SMProduct
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.sku')

sku_router = APIRouter(tags=["Trade Portal"])


@sku_router.get("/kcc-skus", response_model=List[KCCSKU])
def get_kcc_skus(brand_id: Optional[int] = None, is_active: Optional[bool] = None, is_markdown: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        if is_markdown is not None:
            conditions.append("isMarkdown = :is_markdown")
            params["is_markdown"] = int(is_markdown)
        query = "SELECT * FROM dbo.KCCSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [KCCSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching KCCSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/lm-skus", response_model=List[LMSKU])
def get_lm_skus(brand_id: Optional[int] = None, is_active: Optional[bool] = None, is_markdown: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        if is_markdown is not None:
            conditions.append("isMarkdown = :is_markdown")
            params["is_markdown"] = int(is_markdown)
        query = "SELECT * FROM dbo.LMSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [LMSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching LMSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/mg-skus", response_model=List[MGSKU])
def get_mg_skus(brand_id: Optional[int] = None, is_active: Optional[bool] = None, is_markdown: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        if is_markdown is not None:
            conditions.append("isMarkdown = :is_markdown")
            params["is_markdown"] = int(is_markdown)
        query = "SELECT * FROM dbo.MGSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [MGSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching MGSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/rds-skus", response_model=List[RDSSKU])
def get_rds_skus(
    brand_id: Optional[int] = None,
    customer_site_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_markdown: Optional[bool] = None,
):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if customer_site_id is not None:
            conditions.append("customerSiteId = :customer_site_id")
            params["customer_site_id"] = customer_site_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        if is_markdown is not None:
            conditions.append("isMarkdown = :is_markdown")
            params["is_markdown"] = int(is_markdown)
        query = "SELECT * FROM dbo.RDSSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [RDSSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching RDSSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/rds-sale-skus", response_model=List[RDSSaleSKU])
def get_rds_sale_skus(brand_id: Optional[int] = None, customer_site_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if customer_site_id is not None:
            conditions.append("customerSiteId = :customer_site_id")
            params["customer_site_id"] = customer_site_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.RDSSaleSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [RDSSaleSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching RDSSaleSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/sm-skus", response_model=List[SMSKU])
def get_sm_skus(site_id: Optional[int] = None, vendor_code: Optional[str] = None):
    try:
        conditions = []
        params = {}
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        if vendor_code is not None:
            conditions.append("vendorCode = :vendor_code")
            params["vendor_code"] = vendor_code
        query = "SELECT * FROM dbo.SMSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMSKU: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/sm-sku-requests", response_model=List[SMSKURequest])
def get_sm_sku_requests(
    site_id: Optional[int] = None,
    status: Optional[str] = None,
    vendor_code: Optional[str] = None,
):
    try:
        conditions = []
        params = {}
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        if status is not None:
            conditions.append("status = :status")
            params["status"] = status
        if vendor_code is not None:
            conditions.append("vendorCode = :vendor_code")
            params["vendor_code"] = vendor_code
        query = "SELECT * FROM dbo.SMSKURequest"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMSKURequest(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMSKURequest: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/sm-products", response_model=List[SMProduct])
def get_sm_products(stock_no: Optional[str] = None):
    try:
        query = "SELECT * FROM dbo.SMProduct"
        if stock_no is not None:
            query += " WHERE stockNo = :stock_no"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"stock_no": stock_no} if stock_no is not None else {}).fetchall()
            return [SMProduct(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMProducts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@sku_router.get("/sm-products/{bar_code}", response_model=SMProduct)
def get_sm_product(bar_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SMProduct WHERE barCode = :bar_code"),
                {"bar_code": bar_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMProduct not found")
        return SMProduct(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SMProduct {bar_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
