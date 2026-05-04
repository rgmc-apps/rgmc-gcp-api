from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class PackingList(BaseModel):
    packingListId: int
    customerId: Optional[int] = None
    customerLookUpCode: Optional[str] = ""
    brandId: Optional[int] = None
    deliveryDate: Optional[date] = None
    drNumber: Optional[str] = ""
    destnStoreId: Optional[int] = None
    destnSiteId: Optional[int] = None
    filePath: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class PackingListDetail(BaseModel):
    packingListId: int
    productId: int
    productDesc: Optional[str] = ""
    unitPrice: Optional[float] = 0.0
    quantity: Optional[int] = None


class SMDR(BaseModel):
    brandId: int
    drNumber: Optional[str] = ""
    filePath: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None


class SMPackingList(BaseModel):
    brandId: int
    drNumber: Optional[str] = ""
    delDate: Optional[date] = None
    season: Optional[date] = None
    stockNo: Optional[str] = ""
    category: Optional[str] = ""
    description: Optional[str] = ""
    colorCode: Optional[str] = ""
    sizeCode: Optional[str] = ""
    price: Optional[float] = 0.0
    quantity: Optional[int] = None
    filePath: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    siteId: Optional[int] = None
    smStoreCode: Optional[str] = ""
    oldSMStoreCode: Optional[str] = None
