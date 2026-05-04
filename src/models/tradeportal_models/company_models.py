from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Company(BaseModel):
    companyId: int
    companyCode: Optional[str] = ""
    name: Optional[str] = ""
    initials: Optional[str] = ""
    address: Optional[str] = ""
    businessStyle: Optional[str] = ""
    tin: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class CompanyLookUp(BaseModel):
    companyId: int
    customerId: int
    lookUpCode: Optional[str] = ""


class SMCompany(BaseModel):
    smCompanyCode: str
    name: Optional[str] = ""
    tin: Optional[str] = ""
    address: Optional[str] = ""
    contactPerson: Optional[str] = ""
    telephoneNumber: Optional[str] = ""
    faxNumber: Optional[str] = ""
    emailAddress: Optional[str] = ""
    remark: Optional[str] = ""
    customerCompanyId: Optional[int] = None
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
