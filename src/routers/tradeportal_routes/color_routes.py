"""Trade Portal Color Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import ColorGroup, Color, SMColor
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.color')

color_router = APIRouter(tags=["Trade Portal"])


@color_router.get("/color-groups", response_model=List[ColorGroup])
def get_color_groups(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.ColorGroup"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [ColorGroup(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching ColorGroups: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@color_router.get("/color-groups/{color_group_id}", response_model=ColorGroup)
def get_color_group(color_group_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.ColorGroup WHERE colorGroupId = :color_group_id"),
                {"color_group_id": color_group_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ColorGroup not found")
        return ColorGroup(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ColorGroup {color_group_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@color_router.get("/colors", response_model=List[Color])
def get_colors(color_group_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if color_group_id is not None:
            conditions.append("colorGroupId = :color_group_id")
            params["color_group_id"] = color_group_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.Color"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [Color(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching Colors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@color_router.get("/colors/{color_id}", response_model=Color)
def get_color(color_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Color WHERE colorId = :color_id"),
                {"color_id": color_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
        return Color(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching Color {color_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@color_router.get("/sm-colors", response_model=List[SMColor])
def get_sm_colors():
    try:
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text("SELECT * FROM dbo.SMColor")).fetchall()
            return [SMColor(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMColors: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@color_router.get("/sm-colors/{sm_color_code}", response_model=SMColor)
def get_sm_color(sm_color_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SMColor WHERE smColorCode = :sm_color_code"),
                {"sm_color_code": sm_color_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMColor not found")
        return SMColor(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SMColor {sm_color_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
