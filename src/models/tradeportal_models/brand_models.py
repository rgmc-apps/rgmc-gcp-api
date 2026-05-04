from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Brand(BaseModel):
    brandId: int
    brandCode: Optional[str] = ""
    name: Optional[str] = ""
    companyId: Optional[int] = None
    initials: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class BrandLookUpSM(BaseModel):
    brandId: int
    smBrandCode: Optional[str] = ""
    vendorCode: Optional[str] = ""
    deptCode: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    classCode: Optional[str] = ""
    isActive: Optional[bool] = True


class KCCBrandLookUp(BaseModel):
    brandId: int
    vendorCode: Optional[str] = ""


class SMBrandSubClass(BaseModel):
    brandId: int
    subClassCode: Optional[str] = ""
    name: Optional[str] = ""


class LMBrandSiteLookUp(BaseModel):
    brandId: int
    customerSiteId: int
    vendorCode: Optional[str] = ""
    subDeptCode: Optional[str] = ""
    isActive: Optional[bool] = True
