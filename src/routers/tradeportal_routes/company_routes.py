"""Trade Portal Company Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import Company, CompanyLookUp, SMCompany
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.company')

company_router = APIRouter(tags=["Trade Portal"])


@company_router.get("/companies", response_model=List[Company])
def get_companies(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.Company"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [Company(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching companies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@company_router.get("/companies/{company_id}", response_model=Company)
def get_company(company_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Company WHERE companyId = :company_id"),
                {"company_id": company_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return Company(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching company {company_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@company_router.get("/company-lookups", response_model=List[CompanyLookUp])
def get_company_lookups(company_id: Optional[int] = None, customer_id: Optional[int] = None):
    try:
        conditions = []
        params = {}
        if company_id is not None:
            conditions.append("companyId = :company_id")
            params["company_id"] = company_id
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        query = "SELECT * FROM dbo.CompanyLookUp"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [CompanyLookUp(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching CompanyLookUp: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@company_router.get("/sm-companies", response_model=List[SMCompany])
def get_sm_companies(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.SMCompany"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [SMCompany(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching SMCompanies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@company_router.get("/sm-companies/{sm_company_code}", response_model=SMCompany)
def get_sm_company(sm_company_code: str):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.SMCompany WHERE smCompanyCode = :sm_company_code"),
                {"sm_company_code": sm_company_code}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMCompany not found")
        return SMCompany(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SMCompany {sm_company_code}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
