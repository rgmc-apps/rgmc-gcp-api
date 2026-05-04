"""Trade Portal Category Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import ItemGroup, Category, CategoryLookUpSM
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.category')

category_router = APIRouter(tags=["Trade Portal"])


@category_router.get("/item-groups", response_model=List[ItemGroup])
def get_item_groups(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.ItemGroup"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [ItemGroup(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching ItemGroups: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@category_router.get("/item-groups/{item_group_id}", response_model=ItemGroup)
def get_item_group(item_group_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.ItemGroup WHERE itemGroupId = :item_group_id"),
                {"item_group_id": item_group_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ItemGroup not found")
        return ItemGroup(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ItemGroup {item_group_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@category_router.get("/categories", response_model=List[Category])
def get_categories(brand_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.Category"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [Category(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@category_router.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Category WHERE categoryId = :category_id"),
                {"category_id": category_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return Category(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@category_router.get("/category-lookups-sm", response_model=List[CategoryLookUpSM])
def get_category_lookups_sm(brand_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.CategoryLookUpSM"
        if brand_id is not None:
            query += " WHERE brandId = :brand_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"brand_id": brand_id} if brand_id is not None else {}).fetchall()
            return [CategoryLookUpSM(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching CategoryLookUpSM: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
