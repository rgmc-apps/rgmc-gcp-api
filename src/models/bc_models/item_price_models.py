"""Business Central Item Price Pydantic models."""
from typing import Optional
from pydantic import BaseModel


class ItemPriceUpdate(BaseModel):
    unitPrice: Optional[float] = None
    startingDate: Optional[str] = None
    endingDate: Optional[str] = None
    currencyCode: Optional[str] = None
    minimumQuantity: Optional[float] = None
