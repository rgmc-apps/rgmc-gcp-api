"""Trade Portal System Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import (
    Counter, BarcodePrinted, SystemUser, SystemMember,
    SystemAccess, SystemModuleCategory, SystemModule, SystemSetting,
)
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.system')

system_router = APIRouter(tags=["Trade Portal"])


@system_router.get("/counters", response_model=List[Counter])
def get_counters():
    try:
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text("SELECT * FROM dbo.Counter")).fetchall()
            return [Counter(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching counters: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/barcode-printed", response_model=List[BarcodePrinted])
def get_barcode_printed(customer_id: Optional[int] = None, brand_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if brand_id is not None:
            conditions.append("brandId = :brand_id")
            params["brand_id"] = brand_id
        query = "SELECT * FROM dbo.BarcodePrinted"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [BarcodePrinted(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching BarcodePrinted: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-users", response_model=List[SystemUser])
def get_system_users(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.SystemUser"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [SystemUser(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemUsers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-users/{sec_code}", response_model=SystemUser)
def get_system_user(sec_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SystemUser WHERE secCode = :sec_code"),
                {"sec_code": sec_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SystemUser not found")
        return SystemUser(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SystemUser {sec_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-members", response_model=List[SystemMember])
def get_system_members(group_code: Optional[str] = None):
    try:
        query = "SELECT * FROM dbo.SystemMember"
        if group_code is not None:
            query += " WHERE groupCode = :group_code"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"group_code": group_code} if group_code is not None else {}).fetchall()
            return [SystemMember(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemMembers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-access", response_model=List[SystemAccess])
def get_system_access(system_code: Optional[str] = None, sec_code: Optional[str] = None):
    try:
        conditions = []
        params = {}
        if system_code is not None:
            conditions.append("systemCode = :system_code")
            params["system_code"] = system_code
        if sec_code is not None:
            conditions.append("secCode = :sec_code")
            params["sec_code"] = sec_code
        query = "SELECT * FROM dbo.SystemAccess"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SystemAccess(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemAccess: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-module-categories", response_model=List[SystemModuleCategory])
def get_system_module_categories(system_code: Optional[str] = None):
    try:
        query = "SELECT * FROM dbo.SystemModuleCategory"
        if system_code is not None:
            query += " WHERE systemCode = :system_code"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"system_code": system_code} if system_code is not None else {}).fetchall()
            return [SystemModuleCategory(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemModuleCategories: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-modules", response_model=List[SystemModule])
def get_system_modules(system_code: Optional[str] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if system_code is not None:
            conditions.append("systemCode = :system_code")
            params["system_code"] = system_code
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.SystemModule"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [SystemModule(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemModules: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-settings", response_model=List[SystemSetting])
def get_system_settings():
    try:
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text("SELECT * FROM dbo.SystemSetting")).fetchall()
            return [SystemSetting(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SystemSettings: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@system_router.get("/system-settings/{set_code}", response_model=SystemSetting)
def get_system_setting(set_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SystemSetting WHERE setCode = :set_code"),
                {"set_code": set_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SystemSetting not found")
        return SystemSetting(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SystemSetting {set_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
