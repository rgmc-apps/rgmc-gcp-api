"""RGMC custom API — Contact Brand Tag Pydantic models (Pag50209)."""
from pydantic import BaseModel


class ContactBrandTagCreate(BaseModel):
    brandCode: str
