"""Business Central Item Category Pydantic models."""
from typing import Optional
from pydantic import BaseModel


class ItemCategoryCreate(BaseModel):
    code: Optional[str] = None
    displayName: Optional[str] = None
    parentCategory: Optional[str] = None


class ItemCategoryUpdate(BaseModel):
    displayName: Optional[str] = None
    parentCategory: Optional[str] = None
