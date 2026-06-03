"""RGMC custom API — Contact Picture sub-resource endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status
from fastapi.responses import Response
from src.services.bc_functions import (
    rgmc_get_contact_picture,
    rgmc_get_contact_picture_content,
    rgmc_update_contact_picture,
    rgmc_delete_contact_picture,
)

logger = logging.getLogger("bc_routes.contact_pictures")

contact_picture_router = APIRouter(prefix="/bc/custom/contacts", tags=["BC RGMC Contact Pictures"])


@contact_picture_router.get(
    "/{contact_id}/picture",
    summary="Get Contact Picture Metadata",
    operation_id="contact_picture_get_metadata",
)
def get_contact_picture(
    contact_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, data = rgmc_get_contact_picture(contact_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact or picture not found")
        if http_status != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}: {data}",
            )
        if isinstance(data, dict):
            return {"data": data.get("value", data)}
        return {"data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching picture metadata for contact {contact_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@contact_picture_router.get(
    "/{contact_id}/picture/{picture_id}/content",
    summary="Get Contact Picture Content",
    operation_id="contact_picture_get_content",
)
def get_contact_picture_content(
    contact_id: str,
    picture_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status, image_bytes, content_type = rgmc_get_contact_picture_content(
            contact_id, picture_id, company_name=company
        )
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact picture not found")
        if http_status != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
        return Response(content=image_bytes, media_type=content_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching picture content for contact {contact_id}, picture {picture_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@contact_picture_router.patch(
    "/{contact_id}/picture/{picture_id}",
    summary="Upload / Replace Contact Picture",
    operation_id="contact_picture_update",
)
async def update_contact_picture(
    contact_id: str,
    picture_id: str,
    file: UploadFile = File(..., description="Image file to upload"),
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        image_bytes = await file.read()
        content_type = file.content_type or "image/jpeg"
        http_status, data = rgmc_update_contact_picture(
            contact_id, picture_id, image_bytes, content_type, company_name=company
        )
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact picture not found")
        if http_status not in (200, 204):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}: {data}",
            )
        return data or {"detail": "Picture updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating picture for contact {contact_id}, picture {picture_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@contact_picture_router.delete(
    "/{contact_id}/picture/{picture_id}",
    summary="Delete Contact Picture",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="contact_picture_delete",
)
def delete_contact_picture(
    contact_id: str,
    picture_id: str,
    company: Optional[str] = Query(None, description="Override company name"),
):
    try:
        http_status = rgmc_delete_contact_picture(contact_id, picture_id, company_name=company)
        if http_status == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact picture not found")
        if http_status not in (204, 200):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Business Central returned {http_status}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting picture for contact {contact_id}, picture {picture_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
