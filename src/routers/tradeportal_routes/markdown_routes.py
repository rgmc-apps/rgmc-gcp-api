"""Trade Portal Markdown Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import SMMarkdown, SMSaleItemSKU
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.markdown')

markdown_router = APIRouter(tags=["Trade Portal"])


@markdown_router.get("/sm-markdowns", response_model=List[SMMarkdown])
def get_sm_markdowns(brand_id: Optional[int] = None, site_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        query = "SELECT * FROM dbo.SMMarkdown"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMMarkdown(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMMarkdowns: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@markdown_router.get("/sm-sale-item-skus", response_model=List[SMSaleItemSKU])
def get_sm_sale_item_skus(brand_id: Optional[int] = None, site_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if site_id is not None:
            conditions.append("siteId = :site_id")
            params["site_id"] = site_id
        query = "SELECT * FROM dbo.SMSaleItemSKU"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SMSaleItemSKU(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMSaleItemSKUs: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
