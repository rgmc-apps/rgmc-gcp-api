"""Trade Portal Product Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import Season, Size, SMSize, Product, ProductPrice
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.product')

product_router = APIRouter(tags=["Trade Portal"])


@product_router.get("/seasons", response_model=List[Season])
def get_seasons(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.Season"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [Season(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching seasons: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/seasons/{season_id}", response_model=Season)
def get_season(season_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Season WHERE seasonId = :season_id"),
                {"season_id": season_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Season not found")
        return Season(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching season {season_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/sizes", response_model=List[Size])
def get_sizes(item_group_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if item_group_id is not None:
            conditions.append("itemGroupId = :item_group_id")
            params["item_group_id"] = item_group_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.Size"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [Size(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching sizes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/sizes/{size_id}", response_model=Size)
def get_size(size_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Size WHERE sizeId = :size_id"),
                {"size_id": size_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
        return Size(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching size {size_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/sm-sizes", response_model=List[SMSize])
def get_sm_sizes():
    try:
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text("SELECT * FROM dbo.SMSize")).fetchall()
            return [SMSize(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMSizes: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/products", response_model=List[Product])
def get_products(
    brand_id: Optional[int] = None,
    category_id: Optional[int] = None,
    season_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    is_markdown: Optional[bool] = None,
):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if category_id is not None:
            conditions.append("categoryId = :category_id")
            params["category_id"] = category_id
        if season_id is not None:
            conditions.append("seasonId = :season_id")
            params["season_id"] = season_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        if is_markdown is not None:
            conditions.append("isMarkdown = :is_markdown")
            params["is_markdown"] = int(is_markdown)
        query = "SELECT * FROM dbo.Product"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [Product(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Product WHERE productId = :product_id"),
                {"product_id": product_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return Product(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@product_router.get("/product-prices", response_model=List[ProductPrice])
def get_product_prices(product_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if product_id is not None:
            conditions.append("productId = :product_id")
            params["product_id"] = product_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.ProductPrice"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [ProductPrice(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching ProductPrices: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
