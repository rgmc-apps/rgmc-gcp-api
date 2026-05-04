from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SMMarkdown(BaseModel):
    brandId: int
    subClassCode: Optional[str] = ""
    vendorPartStockNo: Optional[str] = ""
    retailAmount: Optional[float] = 0.0
    smStockCode: Optional[str] = ""
    barcode: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
    siteId: Optional[int] = None


class SMSaleItemSKU(BaseModel):
    brandId: int
    subClassCode: Optional[str] = ""
    retailAmount: Optional[float] = 0.0
    smStockCode: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
    siteId: Optional[int] = None
