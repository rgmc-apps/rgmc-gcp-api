"""Trade Portal Customer Routes."""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from src.models.tradeportal_models import Customer, CustomerCompany, CustomerSite, CustomerBarcodeLabel
from ._db import get_tp_engine

logger = logging.getLogger('tradeportal.customer')

customer_router = APIRouter(tags=["Trade Portal"])


@customer_router.get("/customers", response_model=List[Customer])
def get_customers(is_active: Optional[bool] = None):
    try:
        query = "SELECT * FROM dbo.Customer"
        if is_active is not None:
            query += " WHERE isActive = :is_active"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"is_active": int(is_active)} if is_active is not None else {}).fetchall()
            return [Customer(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.Customer WHERE customerId = :customer_id"),
                {"customer_id": customer_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return Customer(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customer-companies", response_model=List[CustomerCompany])
def get_customer_companies(customer_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.CustomerCompany"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [CustomerCompany(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching CustomerCompanies: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customer-companies/{customer_company_id}", response_model=CustomerCompany)
def get_customer_company(customer_company_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.CustomerCompany WHERE customerCompanyId = :customer_company_id"),
                {"customer_company_id": customer_company_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CustomerCompany not found")
        return CustomerCompany(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching CustomerCompany {customer_company_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customer-sites", response_model=List[CustomerSite])
def get_customer_sites(customer_id: Optional[int] = None, is_active: Optional[bool] = None):
    try:
        conditions = []
        params = {}
        if customer_id is not None:
            conditions.append("customerId = :customer_id")
            params["customer_id"] = customer_id
        if is_active is not None:
            conditions.append("isActive = :is_active")
            params["is_active"] = int(is_active)
        query = "SELECT * FROM dbo.CustomerSite"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), params).fetchall()
            return [CustomerSite(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching CustomerSites: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customer-sites/{customer_site_id}", response_model=CustomerSite)
def get_customer_site(customer_site_id: int):
    try:
        with get_tp_engine().connect() as conn:
            row = conn.execute(
                text("SELECT * FROM dbo.CustomerSite WHERE customerSiteId = :customer_site_id"),
                {"customer_site_id": customer_site_id}
            ).fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CustomerSite not found")
        return CustomerSite(**dict(row._mapping))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching CustomerSite {customer_site_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@customer_router.get("/customer-barcode-labels", response_model=List[CustomerBarcodeLabel])
def get_customer_barcode_labels(customer_id: Optional[int] = None):
    try:
        query = "SELECT * FROM dbo.CustomerBarcodeLabel"
        if customer_id is not None:
            query += " WHERE customerId = :customer_id"
        with get_tp_engine().connect() as conn:
            rows = conn.execute(text(query), {"customer_id": customer_id} if customer_id is not None else {}).fetchall()
            return [CustomerBarcodeLabel(**dict(row._mapping)) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching CustomerBarcodeLabels: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
