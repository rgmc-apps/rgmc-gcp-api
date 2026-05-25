"""Business Central Item Pydantic models."""
from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    number: Optional[str] = None
    displayName: Optional[str] = None
    displayName2: Optional[str] = None
    type: Optional[str] = None
    itemCategoryId: Optional[str] = None
    itemCategoryCode: Optional[str] = None
    blocked: Optional[bool] = None
    gtin: Optional[str] = None
    unitPrice: Optional[float] = None
    priceIncludesTax: Optional[bool] = None
    unitCost: Optional[float] = None
    taxGroupId: Optional[str] = None
    taxGroupCode: Optional[str] = None
    baseUnitOfMeasureId: Optional[str] = None
    baseUnitOfMeasureCode: Optional[str] = None
    generalProductPostingGroupId: Optional[str] = None
    generalProductPostingGroupCode: Optional[str] = None
    inventoryPostingGroupId: Optional[str] = None
    inventoryPostingGroupCode: Optional[str] = None


class ItemUpdate(BaseModel):
    number: Optional[str] = None
    displayName: Optional[str] = None
    displayName2: Optional[str] = None
    type: Optional[str] = None
    itemCategoryId: Optional[str] = None
    itemCategoryCode: Optional[str] = None
    blocked: Optional[bool] = None
    gtin: Optional[str] = None
    unitPrice: Optional[float] = None
    priceIncludesTax: Optional[bool] = None
    unitCost: Optional[float] = None
    taxGroupId: Optional[str] = None
    taxGroupCode: Optional[str] = None
    baseUnitOfMeasureId: Optional[str] = None
    baseUnitOfMeasureCode: Optional[str] = None
    generalProductPostingGroupId: Optional[str] = None
    generalProductPostingGroupCode: Optional[str] = None
    inventoryPostingGroupId: Optional[str] = None
    inventoryPostingGroupCode: Optional[str] = None
