"""Business Central data endpoints."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from src.services.bc_functions import call_bc_table, get_dimension_values_by_code, get_access_token

logger = logging.getLogger("bc_routes")

bc_router = APIRouter(prefix="/bc", tags=["Business Central"])


def _unwrap(bc_result: tuple) -> List[Dict[str, Any]]:
    http_status, data = bc_result
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data.get("value", data)


@bc_router.get("/token", summary="Return a valid BC access token")
def get_token():
    try:
        token = get_access_token()
        return {"access_token": token}
    except Exception as e:
        logger.error(f"Error fetching BC access token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bc_router.get("/dimensions", summary="All BC Dimensions (use to verify dimension codes)")
def get_dimensions(company: Optional[str] = Query(None, description="Override company name")):
    try:
        result = call_bc_table("dimensions", company_name=company)
        return {"data": _unwrap(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dimensions: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bc_router.get("/brands", summary="Dimension values for BRAND")
def get_brands(company: Optional[str] = Query(None, description="Override company name")):
    try:
        result = get_dimension_values_by_code("BRAND", company_name=company)
        return {"data": _unwrap(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching brands: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bc_router.get("/departments", summary="Dimension values for DEPARTMENT")
def get_departments(company: Optional[str] = Query(None, description="Override company name")):
    try:
        result = get_dimension_values_by_code("DEPARTMENT", company_name=company)
        return {"data": _unwrap(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@bc_router.get("/contacts", summary="BC Contacts")
def get_contacts(company: Optional[str] = Query(None, description="Override company name")):
    try:
        result = call_bc_table(
            "contacts",
            company_name=company,
        )
        return {"data": _unwrap(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

