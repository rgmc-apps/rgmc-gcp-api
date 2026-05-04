from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class Counter(BaseModel):
    name: str
    value: Optional[int] = None


class BarcodePrinted(BaseModel):
    customerId: int
    customerSiteId: int
    storeTypeId: int
    brandId: int
    stockNumber: Optional[str] = ""
    productId: Optional[int] = None
    batchNumber: Optional[str] = ""
    printType: Optional[str] = ""
    bcodeLabelType: Optional[str] = ""
    requestedQty: Optional[int] = None
    printedQty: Optional[int] = None
    requestBy: Optional[str] = ""
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None


class SystemUser(BaseModel):
    secCode: str
    typeCode: Optional[str] = ""
    name: Optional[str] = ""
    password: Optional[str] = ""
    expirationDate: Optional[date] = None
    graceLoginLeft: Optional[int] = None
    isActive: Optional[bool] = True
    createDate: Optional[datetime] = None
    updateDate: Optional[datetime] = None


class SystemMember(BaseModel):
    groupCode: str
    secCode: Optional[str] = ""


class SystemAccess(BaseModel):
    systemCode: str
    modCode: Optional[str] = ""
    secCode: Optional[str] = ""
    accessRight: Optional[str] = ""


class SystemModuleCategory(BaseModel):
    systemCode: str
    catCode: str
    name: Optional[str] = ""
    type: Optional[str] = ""
    sequenceNumber: Optional[int] = None
    parentCatCode: Optional[str] = ""


class SystemModule(BaseModel):
    systemCode: str
    modCode: str
    name: Optional[str] = ""
    description: Optional[str] = ""
    catCode: Optional[str] = ""
    target: Optional[str] = ""
    sequenceNumber: Optional[int] = None
    supportedRight: Optional[str] = ""
    version: Optional[str] = ""
    isActive: Optional[bool] = True
    createDate: Optional[datetime] = None
    updateDate: Optional[datetime] = None


class SystemSetting(BaseModel):
    setCode: str
    setName: Optional[str] = ""
    setValue: Optional[str] = ""
