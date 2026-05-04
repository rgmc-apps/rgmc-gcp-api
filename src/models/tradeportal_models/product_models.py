from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class Season(BaseModel):
    seasonId: int
    seasonCode: Optional[str] = ""
    name: Optional[str] = ""
    navSeasonCode: Optional[str] = ""
    startMonth: Optional[int] = None
    endMonth: Optional[int] = None
    startPeriod: Optional[date] = None
    endPeriod: Optional[date] = None
    year: Optional[int] = None
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class Size(BaseModel):
    sizeId: int
    sizeCode: Optional[str] = ""
    abbreviation: Optional[str] = ""
    name: Optional[str] = ""
    itemGroupId: Optional[int] = None
    sequenceNumber: Optional[int] = None
    lookUpCode: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class SMSize(BaseModel):
    smSizeCode: str
    lookUpCode: Optional[str] = ""
    remark: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None


class Product(BaseModel):
    productId: int
    brandId: Optional[int] = None
    itemGroupId: Optional[int] = None
    categoryId: Optional[int] = None
    seasonId: Optional[int] = None
    revisedSeasonId: Optional[int] = None
    lineupId: Optional[int] = None
    stockNumber: Optional[str] = ""
    barcode: Optional[str] = ""
    description: Optional[str] = ""
    colorId: Optional[int] = None
    colorBcodeNo: Optional[str] = ""
    sizeId: Optional[int] = None
    sizeBcodeNo: Optional[str] = ""
    originalPrice: Optional[float] = 0.0
    sellingPrice: Optional[float] = 0.0
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class ProductPrice(BaseModel):
    productId: int
    unitPrice: Optional[float] = 0.0
    isMarkdown: Optional[bool] = False
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
