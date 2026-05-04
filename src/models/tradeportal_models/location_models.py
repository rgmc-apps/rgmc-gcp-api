from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Site(BaseModel):
    siteId: int
    siteCode: Optional[str] = ""
    name: Optional[str] = ""


class StoreType(BaseModel):
    storeTypeId: int
    storeTypeCode: Optional[str] = ""
    name: Optional[str] = ""
    initials: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class Store(BaseModel):
    storeId: int
    storeCode: Optional[str] = ""
    name: Optional[str] = ""
    name2: Optional[str] = ""
    storeLocationCode: Optional[str] = ""
    lookUpCode: Optional[str] = ""
    customerId: Optional[int] = None
    customerCompanyId: Optional[int] = None
    customerSiteId: Optional[int] = None
    companyId: Optional[int] = None
    brandId: Optional[int] = None
    storeTypeId: Optional[int] = None
    countryId: Optional[int] = None
    currencyId: Optional[int] = None
    contactPerson: Optional[str] = ""
    address: Optional[str] = ""
    address2: Optional[str] = ""
    cityAddress: Optional[str] = ""
    postalCode: Optional[str] = ""
    phoneNumber: Optional[str] = ""
    faxNumber: Optional[str] = ""
    emailAddress: Optional[str] = ""
    homePageAddress: Optional[str] = ""
    customerPostingGroupId: Optional[int] = None
    generalPostingGroupId: Optional[int] = None
    paymentTermsId: Optional[int] = None
    paymentMethodId: Optional[int] = None
    paymentApplicationMethodId: Optional[int] = None
    tin: Optional[str] = ""
    whtPostingGroupId: Optional[int] = None
    vatPostingGroupId: Optional[int] = None
    globalDimensionId1: Optional[int] = None
    globalDimensionId2: Optional[int] = None
    prePaymentPercent: Optional[float] = 0.0
    shippingAdviceId: Optional[int] = None
    allowLineDiscount: Optional[bool] = False
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None


class SMStore(BaseModel):
    smStoreCode: str
    name: Optional[str] = ""
    initials: Optional[str] = ""
    businessStyle: Optional[str] = ""
    smCompanyCode: Optional[str] = ""
    customerSiteId: Optional[int] = None
    classCode: Optional[str] = ""
    tin: Optional[str] = ""
    address: Optional[str] = ""
    contactPerson: Optional[str] = ""
    telephoneNumber: Optional[str] = ""
    faxNumber: Optional[str] = ""
    emailAddress: Optional[str] = ""
    remark: Optional[str] = ""
    isActive: Optional[bool] = True
    createBy: Optional[str] = ""
    createDate: Optional[datetime] = None
    updateBy: Optional[str] = ""
    updateDate: Optional[datetime] = None
