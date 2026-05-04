from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Customer(BaseModel):
    customerId: int
    customerCode: Optional[str] = ""
    name: Optional[str] = ""
    initials: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class CustomerCompany(BaseModel):
    customerCompanyId: int
    customerCompanyCode: Optional[str] = ""
    name: Optional[str] = ""
    customerId: Optional[int] = None
    lookUpCode: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class CustomerSite(BaseModel):
    customerSiteId: int
    customerSiteCode: Optional[str] = ""
    name: Optional[str] = ""
    customerId: Optional[int] = None
    lookUpCode: Optional[str] = ""
    initials: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class CustomerBarcodeLabel(BaseModel):
    customerId: int
    storeTypeId: int
    productType: Optional[str] = ""
    labelType: Optional[str] = ""
    qtyPerRow: Optional[int] = None
    storedProcedure: Optional[str] = ""
