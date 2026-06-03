"""RGMC custom API — Contact endpoints (Pag50203)."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from src.services.bc_functions import (
    call_rgmc_table,
    rgmc_get_record,
    rgmc_create_record,
    rgmc_update_record,
    rgmc_delete_record,
    rgmc_get_contact_picture,
    rgmc_get_contact_picture_content,
    rgmc_update_contact_picture,
)
from src.models.bc_models import RgmcContactCreate, RgmcContactUpdate

logger = logging.getLogger("bc_routes.rgmc_contacts")

rgmc_contact_router = APIRouter(prefix="/bc/custom/contacts", tags=["BC RGMC Contacts"])

_TABLE = "contacts"


def _unwrap_list(bc_result: tuple) -> List[Dict[str, Any]]:
    http_status, data = bc_result
    if http_status != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data.get("value", data)


def _unwrap_single(http_status: int, data: Any) -> Dict[str, Any]:
    if http_status == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    if http_status not in (200, 201):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Business Central returned {http_status}: {data}",
        )
    return data


@rgmc_contact_router.get("", summary="List RGMC Contacts")
def list_rgmc_contacts(
    company: Optional[str] = Query(None, description="Override company name"),
    filter: Optional[str] = Query(None, description="OData $filter expression"),
    select: Optional[str] = Query(None, description="OData $select"),
):
    try:
        result = call_rgmc_table(_TABLE, company_name=company, odata_filter=filter, select=select)
        return {"data": _unwrap_list(result)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing RGMC contacts: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.get("/{contact_id}", summary="Get RGMC Contact by ID")
def get_rgmc_contact(
    contact_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_get_record(_TABLE, contact_id, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching RGMC contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.post("", summary="Create RGMC Contact", status_code=status.HTTP_201_CREATED)
def create_rgmc_contact(
    body: RgmcContactCreate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        http_status, data = rgmc_create_record(_TABLE, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating RGMC contact: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.patch("/{contact_id}", summary="Update RGMC Contact")
def update_rgmc_contact(
    contact_id: str,
    body: RgmcContactUpdate,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        payload = body.model_dump(exclude_none=True)
        if not payload:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update")
        http_status, data = rgmc_update_record(_TABLE, contact_id, payload, company_name=company)
        return _unwrap_single(http_status, data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating RGMC contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.get("/{contact_id}/picture", summary="Get RGMC Contact Picture")
def get_contact_picture(
    contact_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        meta_status, meta_data = rgmc_get_contact_picture(contact_id, company_name=company)
        pictures = meta_data.get("value", []) if meta_status == 200 else []
        if not pictures:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No picture found")
        picture_id = pictures[0]["id"]
        img_status, img_bytes, content_type = rgmc_get_contact_picture_content(contact_id, picture_id, company_name=company)
        if img_status != 200 or not img_bytes:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Picture content not available")
        return Response(content=img_bytes, media_type=content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching picture for contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.patch("/{contact_id}/picture", summary="Update RGMC Contact Picture")
async def update_contact_picture(
    contact_id: str,
    file: UploadFile = File(...),
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        meta_status, meta_data = rgmc_get_contact_picture(contact_id, company_name=company)
        pictures = meta_data.get("value", []) if meta_status == 200 else []
        if not pictures:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No picture record found for contact")
        picture_id = pictures[0]["id"]
        image_bytes = await file.read()
        content_type = file.content_type or "image/jpeg"
        upd_status, upd_data = rgmc_update_contact_picture(
            contact_id, picture_id, image_bytes, content_type, company_name=company
        )
        if upd_status not in (200, 204):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"BC returned {upd_status}: {upd_data}")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating picture for contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@rgmc_contact_router.delete("/{contact_id}", summary="Delete RGMC Contact", status_code=status.HTTP_204_NO_CONTENT)
def delete_rgmc_contact(
    contact_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = rgmc_delete_record(_TABLE, contact_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting RGMC contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
